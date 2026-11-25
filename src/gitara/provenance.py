"""Provenance records for experiment runs.

Each run gets a new directory ``results/runs/<id>/`` at the top of the git work tree.
``start_run`` creates it and writes ``run.json`` with status ``"running"``, so a crashed run
still leaves a record. It also writes ``uncommitted.diff`` when the work tree differs from the
commit; ``git apply`` on a checkout of that commit restores the code that ran, including
untracked, non-ignored files. Artifacts of the run go into the same directory.
``finish_run`` writes the final status once and refuses to change a finished run::

    record = start_run("convergence", config, seeds=[0, 1])
    try:
        results = ...
    except Exception as error:
        finish_run(record, "failed", errors=[repr(error)])
        raise
    finish_run(record, "ok", results)

Data source, license and preprocessing belong in ``config``; this module does not guess them.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import secrets
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Status = Literal["ok", "failed"]

THREAD_VARIABLES = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
RUNS_DIR = Path("results", "runs")
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
# Explicit flags keep the patch applicable whatever the user's diff configuration is.
DIFF_FLAGS = (
    "--binary", "--no-color", "--no-ext-diff", "--no-textconv",
    "--src-prefix=a/", "--dst-prefix=b/",
)


def start_run(
    name: str,
    config: Any,
    *,
    seeds: Sequence[int],
    manifest: str | os.PathLike[str] | None = None,
    root: str | os.PathLike[str] = ".",
) -> dict[str, Any]:
    """Create the run directory and return the record of the starting state.

    ``config`` must be JSON-serializable. ``seeds`` lists every random seed of the run and is
    empty only for a deterministic run. ``manifest`` is the data manifest whose MD5 is
    recorded; ``None`` records that no manifest was used. ``root`` is any directory inside
    the git work tree.
    """
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError("name must be letters, digits, '_', '.' or '-', starting alphanumeric")
    config = _json_copy(config, "config")
    if isinstance(seeds, (str, bytes)) or not all(
        isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds
    ):
        raise ValueError("seeds must be a sequence of integers")

    top = Path(_git(Path(root), "rev-parse", "--show-toplevel").decode().strip())
    commit = _git(top, "rev-parse", "HEAD").decode().strip()
    patch = _uncommitted_patch(top)
    data_manifest = None
    if manifest is not None:
        path = Path(manifest)
        data_manifest = {"path": str(path), "md5": hashlib.md5(path.read_bytes()).hexdigest()}

    started = datetime.now(UTC)
    run_id = _run_id(name, started)
    run_dir = top / RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    if patch:
        (run_dir / "uncommitted.diff").write_bytes(patch)

    record = {
        "id": run_id,
        "name": name,
        "dir": str(run_dir),
        "status": "running",
        "started": started.isoformat(timespec="seconds"),
        "command": sys.orig_argv,
        "config": config,
        "seeds": list(seeds),
        "data_manifest": data_manifest,
        "git": {
            "commit": commit,
            "dirty": bool(patch),
            "diff": "uncommitted.diff" if patch else None,
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "threads": {variable: os.environ.get(variable) for variable in THREAD_VARIABLES},
            "packages": _packages(),
        },
    }
    _write_record(run_dir, record)
    return record


def finish_run(
    record: dict[str, Any],
    status: Status,
    results: Any = None,
    errors: Sequence[str] = (),
) -> Path:
    """Write the final record of a running run and return its directory.

    A failed run needs at least one error message. A finished run is never rewritten.
    """
    if status not in ("ok", "failed"):
        raise ValueError("status must be 'ok' or 'failed'")
    if isinstance(errors, str) or not all(isinstance(error, str) for error in errors):
        raise ValueError("errors must be a sequence of strings")
    if status == "failed" and not errors:
        raise ValueError("a failed run needs an error message")
    results = _json_copy(results, "results")

    run_dir = Path(record["dir"])
    if json.loads((run_dir / "run.json").read_text(encoding="utf-8"))["status"] != "running":
        raise FileExistsError(f"run {record['id']} is already finished")
    _write_record(run_dir, {
        **record,
        "status": status,
        "finished": datetime.now(UTC).isoformat(timespec="seconds"),
        "results": results,
        "errors": list(errors),
    })
    return run_dir


def _run_id(name: str, started: datetime) -> str:
    return f"{started:%Y%m%dT%H%M%SZ}-{name}-{secrets.token_hex(3)}"


def _json_copy(value: Any, label: str) -> Any:
    try:
        return json.loads(json.dumps(value))
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{label} must be JSON-serializable (convert NumPy arrays and integers): {error}"
        ) from error


def _git(cwd: Path, *args: str, ok: tuple[int, ...] = (0,)) -> bytes:
    try:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False)
    except FileNotFoundError as error:
        raise RuntimeError("provenance requires git on PATH") from error
    if result.returncode not in ok:
        message = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed in {cwd}: {message}")
    return result.stdout


def _uncommitted_patch(top: Path) -> bytes:
    patch = _git(top, "diff", *DIFF_FLAGS, "HEAD")
    untracked = _git(top, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    for path in filter(None, untracked):
        # --no-index exits with 1 when the files differ, which is always the case here.
        patch += _git(
            top, "diff", *DIFF_FLAGS, "--no-index", "--", os.devnull, os.fsdecode(path), ok=(1,)
        )
    return patch


def _packages() -> dict[str, str]:
    versions = {dist.metadata["Name"]: dist.version for dist in importlib.metadata.distributions()}
    return dict(sorted(versions.items(), key=lambda item: item[0].lower()))


def _write_record(run_dir: Path, record: dict[str, Any]) -> None:
    temporary = run_dir / "run.json.tmp"
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(run_dir / "run.json")
