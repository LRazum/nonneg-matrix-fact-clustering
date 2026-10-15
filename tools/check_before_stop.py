#!/usr/bin/env python3
"""Run the shared local checks; --hook uses the Stop-hook JSON protocol.

The numerical stack has not been selected yet. Until pyproject.toml exists, project
checks are explicitly NOT RUN. Adding that file requires tools/check_project.py,
which must run the agreed checks in the agreed environment and propagate failures.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAIL_LINES = 200
TIMEOUT_SECONDS = 500
NOT_RUN_REASON_RE = re.compile(r"^SKIPPED \[\d+\] [^\n]*?NOT RUN: (.+)$", re.M)


def steps() -> list[tuple[str, list[str], Path]]:
    found = [
        ("documentation check", [sys.executable, "tools/check_docs.py"], ROOT),
        (
            "workflow tools tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py"],
            ROOT,
        ),
    ]
    if (ROOT / "pyproject.toml").is_file() and (ROOT / "tools/check_project.py").is_file():
        found.append(("project checks", [sys.executable, "tools/check_project.py"], ROOT))
    return found


def tail(text: str) -> str:
    lines = text.rstrip().splitlines()
    if len(lines) <= TAIL_LINES:
        return "\n".join(lines)
    return f"... ({len(lines) - TAIL_LINES} earlier lines cut)\n" + "\n".join(lines[-TAIL_LINES:])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hook", action="store_true", help="emit only Stop-hook JSON on success")
    args = parser.parse_args(argv)
    failures: list[str] = []
    not_run: list[str] = []
    if not (ROOT / "pyproject.toml").is_file():
        not_run.append(
            "project checks NOT RUN: no pyproject.toml; the Python stack and numerical checks "
            "have not been agreed yet"
        )
    elif not (ROOT / "tools/check_project.py").is_file():
        failures.append(
            "== project checks NOT RUN: pyproject.toml exists but tools/check_project.py is "
            "missing. Configure that runner with the agreed environment and checks."
        )
    for name, command, cwd in steps():
        try:
            result = subprocess.run(
                command, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            failures.append(f"== {name} could not complete: {' '.join(command)}\n{error}")
            continue
        output = tail(result.stdout + ("\n" if result.stdout else "") + result.stderr)
        if result.returncode != 0:
            failures.append(f"== {name} failed (exit {result.returncode}): {' '.join(command)}\n{output}")
        else:
            reasons = sorted(set(NOT_RUN_REASON_RE.findall(result.stdout + "\n" + result.stderr)))
            if reasons:
                not_run.append(f"{name}: some tests NOT RUN ({'; '.join(reasons)})")
            if not args.hook:
                print(f"PASS: {name}")
    if failures:
        print(
            "Checks failed. Fix them before finishing.\n\n"
            + "\n\n".join(failures + [f"== {line}" for line in not_run]),
            file=sys.stderr,
        )
        return 2
    if args.hook:
        report = {"systemMessage": "check_before_stop: " + "; ".join(not_run) + "."} if not_run else {}
        print(json.dumps(report))
    elif not_run:
        print("\n".join(not_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
