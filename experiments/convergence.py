"""B5: the multiplicative updates on real GuitarSet spectrograms.

Run from the repository root, after ``uv run python -m gitara.data download``::

    uv run python -m experiments.convergence

Only the training players of one leave-one-player-out fold are read; the held-out player
is never loaded. Two settings are studied:

* ``unsupervised``: one recording, random positive ``W0`` and ``H0`` of rank ``--rank``;
* ``masked``: template learning on a seeded sample of training recordings. ``H0`` is the
  piano-roll mask with an always-active background row and ``W0`` is drawn from
  ``uniform(0.5, 1.5)``, as planned for ``gitara.templates`` (C3). A pitch without any
  labelled frame gets a zero column in ``W0``.

Every (objective, eps, seed) combination runs ``fit`` with ``tol=0`` for ``--max-iter``
(``--masked-max-iter``) iterations. The iterates do not depend on ``tol``, so one objective history shows where
``fit`` would stop for every tolerance in ``TOLS``. A failed combination, e.g. a zero
denominator with ``eps=0``, is recorded and reported, not skipped. The peak memory that
``fit`` allocates on top of the data is measured in a separate short run with
``tracemalloc``, so that tracing does not distort the timing.

Outputs go to the provenance directory ``results/runs/<id>/``: ``run.json`` with the
summary, ``curves.json`` with every objective history and one figure per setting.
``--publish results/runs/<id>`` copies the figures of a finished run of committed code and
its record, without local absolute paths, to ``results/convergence/`` for the seminar.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
import tracemalloc
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from gitara.data import DEFAULT_MANIFEST, DEFAULT_ROOT, MODES, Track, list_tracks, load_audio, load_notes
from gitara.nmf import fit, frobenius, kl_divergence
from gitara.provenance import finish_run, start_run
from gitara.spectrogram import F_MAX, HOP, N_WIN, PITCHES, SAMPLE_RATE, piano_roll, stft_magnitude

OBJECTIVES = ("kl", "frobenius")
EPS_VALUES = (1e-12, 1e-9, 0.0)
TOLS = (1e-3, 1e-4, 1e-5)
# Annotations with a constant offset (marl/GuitarSet#5); exclusion proposed in issue #7.
SHIFTED_TRACKS = ("04_BN3-154-E_comp", "04_Jazz1-200-B_comp")
MEMORY_ITERATIONS = 2
PUBLISHED = Path("results", "convergence")
FIGURES = ("unsupervised.png", "masked.png")


def max_relative_increase(history: Sequence[float]) -> float:
    """Largest ``(f[t] - f[t-1]) / f[t-1]`` over the history, or 0.0 if it never increases."""
    f = np.asarray(history, dtype=np.float64)
    previous, current = f[:-1], f[1:]
    change = np.divide(current - previous, previous, out=np.zeros_like(previous), where=previous > 0)
    return float(max(change.max(initial=0.0), 0.0))


def stopping_iteration(history: Sequence[float], tol: float) -> int | None:
    """Iteration at which ``fit(..., tol=tol)`` stops, or None if not within the history.

    Mirrors the rule in ``fit``: stop after the first iteration whose objective does not
    increase and whose relative drop is below ``tol``.
    """
    for t in range(1, len(history)):
        previous, current = history[t - 1], history[t]
        if current <= previous and (previous - current) / previous < tol:
            return t
    return None


def mask_from_roll(roll: NDArray[np.bool_], background: bool = True) -> NDArray[np.float64]:
    """Return the activation mask of shape ``(K, n)``, or ``(K + 1, n)`` with background."""
    mask = np.asarray(roll, dtype=np.float64)
    if background:
        mask = np.vstack((mask, np.ones((1, mask.shape[1]))))
    return mask


def masked_start(
    rolls: Sequence[NDArray[np.bool_]], m: int, rng: np.random.Generator,
) -> tuple[NDArray[np.float64], list[NDArray[np.float64]]]:
    """Return ``(W0, H0s)`` for template learning with a background component.

    ``H0`` of each block is its mask. ``W0`` is ``uniform(0.5, 1.5)`` in the columns of
    pitches labelled in at least one frame and of the background, and zero elsewhere.
    """
    available = np.append(np.any([roll.any(axis=1) for roll in rolls], axis=0), True)
    W0 = rng.uniform(0.5, 1.5, size=(m, available.size)) * available
    return W0, [mask_from_roll(roll) for roll in rolls]


def run_setting(
    blocks: Sequence[NDArray], W0: NDArray, H0s: Sequence[NDArray], *,
    objective: str, eps: float, max_iter: int,
) -> dict[str, Any]:
    """Run ``fit`` with ``tol=0`` and summarize its history; a numerical failure is returned."""
    start = time.perf_counter()
    try:
        result = fit(blocks, W0, H0s, objective=objective, eps=eps, max_iter=max_iter, tol=0)
    except FloatingPointError as error:
        return {"status": "failed", "error": repr(error), "seconds": time.perf_counter() - start}
    seconds = time.perf_counter() - start
    # fit evaluates the objective once per iteration; time one evaluation to separate it.
    loss = kl_divergence if objective == "kl" else frobenius
    start = time.perf_counter()
    for block, H in zip(blocks, result.Hs, strict=True):
        loss(block, result.W @ H)
    objective_seconds = time.perf_counter() - start
    history = result.objective
    stops = {tol: stopping_iteration(history, tol) for tol in TOLS}
    final = history[-1]
    return {
        "status": "ok",
        "n_iter": result.n_iter,
        "stop_reason": result.stop_reason,
        "seconds": seconds,
        "seconds_per_iter": seconds / result.n_iter if result.n_iter else None,
        "objective_seconds": objective_seconds,
        "initial": history[0],
        "final": final,
        "max_relative_increase": max_relative_increase(history),
        "stop_at": {str(tol): t for tol, t in stops.items()},
        # Relative excess over the final value when stopping early; final > 0 on real data.
        "gap_at_stop": {
            str(tol): None if t is None or final == 0 else (history[t] - final) / final
            for tol, t in stops.items()
        },
        "inactive": list(result.inactive),
        "history": list(history),
    }


def peak_memory(blocks: Sequence[NDArray], W0: NDArray, H0s: Sequence[NDArray], objective: str) -> int:
    """Peak bytes allocated by a short ``fit`` run, excluding the data already in memory."""
    tracemalloc.start()
    try:
        fit(blocks, W0, H0s, objective=objective, max_iter=MEMORY_ITERATIONS, tol=0)
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def spectrogram_and_roll(track: Track) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    A, _, times = stft_magnitude(load_audio(track))
    intervals, pitches, _ = load_notes(track)
    return A, piano_roll(intervals, pitches, times)


def training_sample(
    tracks: Sequence[Track], held_out: int, per_group: int, rng: np.random.Generator,
) -> list[Track]:
    """Draw ``per_group`` tracks per (training player, mode), skipping shifted annotations."""
    chosen = []
    for player in sorted({track.player for track in tracks} - {held_out}):
        for mode in MODES:
            group = [
                track for track in tracks
                if track.player == player and track.mode == mode and track.track_id not in SHIFTED_TRACKS
            ]
            chosen += [group[i] for i in sorted(rng.choice(len(group), size=per_group, replace=False))]
    return chosen


def study(
    blocks: Sequence[NDArray], starts: dict[int, tuple[NDArray, list[NDArray]]], max_iter: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Run every (objective, eps, seed) combination from the given starting factors."""
    runs = []
    for objective in OBJECTIVES:
        for eps in EPS_VALUES:
            for seed, (W0, H0s) in starts.items():
                summary = run_setting(blocks, W0, H0s, objective=objective, eps=eps, max_iter=max_iter)
                runs.append({"objective": objective, "eps": eps, "seed": seed, **summary})
                print(_describe(runs[-1]), flush=True)
    W0, H0s = next(iter(starts.values()))
    memory = {objective: peak_memory(blocks, W0, H0s, objective) for objective in OBJECTIVES}
    return runs, memory


def _describe(run: dict[str, Any]) -> str:
    label = f"{run['objective']:>9} eps={run['eps']:<6g} seed={run['seed']}"
    if run["status"] != "ok":
        return f"{label}  FAILED  {run['error']}"
    return (
        f"{label}  {run['n_iter']} it  {run['seconds_per_iter'] * 1e3:.1f} ms/it  "
        f"max increase {run['max_relative_increase']:.1e}  stop at {run['stop_at']}"
    )


def plot_setting(runs: Sequence[dict[str, Any]], title: str, path: Path) -> None:
    """Objective and relative drop per iteration; rows are objectives, colour and dash is eps."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid = "#0b0b0b", "#898781", "#e1e0d9"
    styles = dict(zip(EPS_VALUES, (("#2a78d6", "-"), ("#eb6834", "--"), ("#1baf7a", ":"))))
    fig, axes = plt.subplots(len(OBJECTIVES), 2, figsize=(10, 3.4 * len(OBJECTIVES)), squeeze=False)
    fig.patch.set_facecolor("#fcfcfb")
    for row, objective in enumerate(OBJECTIVES):
        value_ax, drop_ax = axes[row]
        labelled: set[float] = set()
        for run in runs:
            if run["objective"] != objective or run["status"] != "ok":
                continue
            color, dash = styles[run["eps"]]
            f = np.asarray(run["history"])
            # One legend entry per eps; the seeds share its colour and dash.
            label = None if run["eps"] in labelled else f"ε = {run['eps']:g}"
            labelled.add(run["eps"])
            iterations = np.arange(f.size)
            value_ax.plot(iterations, f, color=color, linestyle=dash, linewidth=2, label=label)
            drop = (f[:-1] - f[1:]) / f[:-1]
            positive = drop > 0
            drop_ax.plot(iterations[1:][positive], drop[positive], color=color, linestyle=dash, linewidth=2)
        for tol in TOLS:
            drop_ax.axhline(tol, color=muted, linewidth=1)
            drop_ax.annotate(f"tol {tol:g}", (1, tol), xycoords=("axes fraction", "data"),
                             xytext=(-4, 3), textcoords="offset points", ha="right", color=muted, fontsize=8)
        name = "KL" if objective == "kl" else "Frobenius"
        value_ax.set_ylabel(f"{name}: funkcija cilja")
        drop_ax.set_ylabel(f"{name}: relativni pad")
        value_ax.legend(frameon=False, labelcolor=ink)
        for ax in (value_ax, drop_ax):
            ax.set_yscale("log")
            ax.set_xlabel("iteracija")
            ax.set_facecolor("#fcfcfb")
            ax.grid(color=grid, linewidth=0.8)
            ax.tick_params(colors=muted, labelcolor=ink)
            for spine in ax.spines.values():
                spine.set_color(grid)
    fig.suptitle(title, color=ink)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def publish(run_dir: Path, out_dir: Path = PUBLISHED) -> None:
    """Copy the figures and the record of a finished run, without local paths, to ``out_dir``."""
    record = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    if record["status"] != "ok" or record["git"]["dirty"]:
        raise ValueError(f"run {record['id']} must have finished ok on a clean work tree")
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in FIGURES:
        shutil.copy2(run_dir / name, out_dir / name)
    del record["dir"]
    record["command"] = ["python", *record["command"][1:]]
    text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "summary.json").write_text(text, encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="GuitarSet folder")
    parser.add_argument("--held-out-player", type=int, default=5, help="never loaded")
    parser.add_argument("--unsupervised-track", default="00_BN1-129-Eb_comp")
    parser.add_argument("--rank", type=int, default=len(PITCHES), help="unsupervised rank")
    parser.add_argument("--tracks-per-group", type=int, default=2,
                        help="masked: tracks per training (player, mode)")
    parser.add_argument("--selection-seed", type=int, default=0, help="masked: track sample")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2], help="initializations")
    parser.add_argument("--max-iter", type=int, default=2000, help="unsupervised iterations")
    parser.add_argument("--masked-max-iter", type=int, default=200, help="masked iterations")
    parser.add_argument("--publish", type=Path, metavar="RUN_DIR",
                        help=f"copy a finished run to {PUBLISHED} instead of running")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.publish:
        publish(args.publish)
        return
    tracks = {track.track_id: track for track in list_tracks(args.root)}
    unsupervised = tracks[args.unsupervised_track]
    if unsupervised.player == args.held_out_player:
        raise ValueError(f"{unsupervised.track_id} belongs to the held-out player")
    sample = training_sample(
        list(tracks.values()), args.held_out_player, args.tracks_per_group,
        np.random.default_rng(args.selection_seed),
    )
    config = {
        "data": "GuitarSet 1.1.0, audio_mono-mic, data/README.md",
        "preprocessing": {
            "sample_rate": SAMPLE_RATE, "n_win": N_WIN, "hop": HOP, "f_max": F_MAX,
            "magnitude": "STFT magnitude, no level normalization",
            "pitches": [int(PITCHES[0]), int(PITCHES[-1])],
        },
        "held_out_player": args.held_out_player,
        "objectives": list(OBJECTIVES),
        "eps": list(EPS_VALUES),
        "tol": 0,
        "tols_evaluated": list(TOLS),
        "normalize": True,
        "unsupervised": {
            "track": unsupervised.track_id, "rank": args.rank, "max_iter": args.max_iter,
            "init": "W0, H0 uniform(0.5, 1.5)",
        },
        "masked": {
            "max_iter": args.masked_max_iter,
            "tracks_per_group": args.tracks_per_group,
            "selection_seed": args.selection_seed,
            "excluded": list(SHIFTED_TRACKS),
            "tracks": [track.track_id for track in sample],
            "init": "W0 uniform(0.5, 1.5) on labelled pitches and background, H0 = mask",
            "background": True,
        },
        "init_seeds": args.seeds,
    }
    seeds = sorted({*args.seeds, args.selection_seed})
    record = start_run("convergence", config, seeds=seeds, manifest=DEFAULT_MANIFEST)
    run_dir = Path(record["dir"])
    try:
        results, curves = _experiment(args, unsupervised, sample, run_dir)
    except Exception as error:
        finish_run(record, "failed", errors=[repr(error)])
        raise
    (run_dir / "curves.json").write_text(json.dumps(curves), encoding="utf-8")
    failures = [
        f"{name}: {run['objective']} eps={run['eps']} seed={run['seed']}: {run['error']}"
        for name, setting in results.items() for run in setting["runs"] if run["status"] != "ok"
    ]
    finish_run(record, "ok", results, errors=failures)
    print(f"Zapis pokretanja: {run_dir}")


def _experiment(
    args: argparse.Namespace, unsupervised: Track, sample: Sequence[Track], run_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    results: dict[str, Any] = {}
    curves: dict[str, Any] = {}

    A, _ = spectrogram_and_roll(unsupervised)
    m, n = A.shape
    starts = {}
    for seed in args.seeds:
        rng = np.random.default_rng(seed)
        starts[seed] = (rng.uniform(0.5, 1.5, (m, args.rank)), [rng.uniform(0.5, 1.5, (args.rank, n))])
    print(f"unsupervised: {unsupervised.track_id}, A {m}x{n}, rank {args.rank}", flush=True)
    runs, memory = study([A], starts, args.max_iter)
    results["unsupervised"] = {"shape": [m, n], "data_bytes": A.nbytes, "peak_fit_bytes": memory}

    pairs = [spectrogram_and_roll(track) for track in sample]
    blocks, rolls = [A for A, _ in pairs], [roll for _, roll in pairs]
    n_frames = sum(block.shape[1] for block in blocks)
    starts = {seed: masked_start(rolls, m, np.random.default_rng(seed)) for seed in args.seeds}
    labelled = np.any([roll.any(axis=1) for roll in rolls], axis=0)
    print(f"masked: {len(blocks)} tracks, {n_frames} frames, {int(labelled.sum())} labelled pitches", flush=True)
    masked_runs, masked_memory = study(blocks, starts, args.masked_max_iter)
    results["masked"] = {
        "shape": [m, n_frames],
        "data_bytes": sum(block.nbytes for block in blocks),
        "unlabelled_pitches": PITCHES[~labelled].tolist(),
        "peak_fit_bytes": masked_memory,
    }

    for name, setting_runs in (("unsupervised", runs), ("masked", masked_runs)):
        curves[name] = [
            {key: run[key] for key in ("objective", "eps", "seed", "history")}
            for run in setting_runs if run["status"] == "ok"
        ]
        results[name]["runs"] = [{k: v for k, v in run.items() if k != "history"} for run in setting_runs]
        title = (f"Bez nadzora: {unsupervised.track_id}, r = {args.rank}" if name == "unsupervised"
                 else f"S maskom: {len(blocks)} snimki gitarista za učenje")
        plot_setting(setting_runs, title, run_dir / f"{name}.png")
    return results, curves


if __name__ == "__main__":
    main()
