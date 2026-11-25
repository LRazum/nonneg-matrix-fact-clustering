"""B6, masked part: stability of learned templates across seeds and folds.

Run from the repository root, after ``uv run python -m gitara.data download``::

    uv run python -m experiments.template_stability

Templates are learned by masked NMF with an always-active background component. Until
``gitara.templates`` (C3) is merged, ``learn_masked`` stands in for ``learn_templates``: the
start planned for C3 (``experiments.convergence.masked_start``) followed by ``fit``. When C3
arrives, only ``learn_masked`` changes.

One sample of ``--tracks-per-group`` recordings per (player, mode) is drawn once. The fold of
test player g learns from the sampled recordings of the other players, as in the outer
leave-one-player-out split; this script only describes stability and selects nothing. The
mask fixes the order of the components, so template k is compared directly between runs: the
mean and smallest pairwise cosine similarity across seeds within each fold, and across folds
for each seed. A pitch unlabelled in some of the compared training sets has no value.

Outputs go to the provenance directory ``results/runs/<id>/``: ``run.json``,
``templates.npz`` with every learned ``W`` and ``template_stability.png``.
"""
from __future__ import annotations

import argparse
import time
import warnings
from collections.abc import Sequence
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from experiments.convergence import SHIFTED_TRACKS, masked_start, spectrogram_and_roll, training_sample
from gitara.data import DEFAULT_MANIFEST, DEFAULT_ROOT, N_PLAYERS, Track, list_tracks
from gitara.nmf import fit
from gitara.provenance import finish_run, start_run
from gitara.spectrogram import F_MAX, HOP, N_WIN, PITCHES, SAMPLE_RATE

OBJECTIVES = ("kl", "frobenius")


def learn_masked(
    blocks: Sequence[NDArray], rolls: Sequence[NDArray], *,
    objective: str, seed: int, max_iter: int, tol: float,
) -> tuple[NDArray[np.float64], int]:
    """Stand-in for ``gitara.templates.learn_templates`` (C3); returns ``(W, n_iter)``.

    ``W`` has shape ``(m, K + 1)``: templates in ``PITCHES`` order and the background last.
    A pitch without labelled frames has a zero column.
    """
    W0, H0s = masked_start(rolls, blocks[0].shape[0], np.random.default_rng(seed))
    result = fit(blocks, W0, H0s, objective=objective, max_iter=max_iter, tol=tol)
    return result.W, result.n_iter


def pairwise_similarity(Ws: Sequence[NDArray]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Mean and smallest cosine similarity of column k over all pairs of the given matrices.

    The value is NaN for a column that is zero in any of them.
    """
    stacked = np.stack([np.asarray(W, dtype=np.float64) for W in Ws])
    norms = np.linalg.norm(stacked, axis=1)  # (runs, columns)
    present = np.all(norms > 0, axis=0)
    unit = np.divide(stacked, norms[:, None, :], out=np.zeros_like(stacked), where=norms[:, None, :] > 0)
    pairs = np.array([np.sum(unit[i] * unit[j], axis=0) for i, j in combinations(range(len(Ws)), 2)])
    mean = np.where(present, pairs.mean(axis=0), np.nan)
    smallest = np.where(present, pairs.min(axis=0), np.nan)
    return mean, smallest


def fold_tracks(sample: Sequence[Track], test_player: int) -> list[Track]:
    """Training recordings of the fold whose test player is ``test_player``."""
    return [track for track in sample if track.player != test_player]


def _json_values(values: NDArray) -> list[float | None]:
    return [None if np.isnan(value) else float(value) for value in values]


def plot(summary: dict[str, dict[str, Any]], title: str, path: Path) -> None:
    """Per pitch: across seeds (median over folds) and across folds (first seed)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid = "#0b0b0b", "#898781", "#e1e0d9"
    series = (("across_seeds_median", "kroz sjemena (medijan po foldovima)", "#2a78d6", "o"),
              ("across_folds_first_seed", "kroz foldove (prvo sjeme)", "#eb6834", "s"))
    fig, axes = plt.subplots(1, len(summary), figsize=(6 * len(summary), 3.8), squeeze=False)
    fig.patch.set_facecolor("#fcfcfb")
    for ax, (objective, values) in zip(axes[0], summary.items()):
        for key, label, color, marker in series:
            y = np.array([np.nan if v is None else v for v in values[key]], dtype=np.float64)
            ax.plot(PITCHES, y[: len(PITCHES)], color=color, marker=marker, markersize=4,
                    linewidth=1.5, label=label)
        ax.set_title("KL" if objective == "kl" else "Frobenius", color=ink)
        ax.set_xlabel("MIDI visina")
        ax.set_ylabel("srednja kosinusna sličnost predložaka")
        ax.set_ylim(0, 1.02)
        ax.legend(frameon=False, labelcolor=ink, fontsize=8, loc="lower left")
        ax.set_facecolor("#fcfcfb")
        ax.grid(color=grid, linewidth=0.8)
        ax.tick_params(colors=muted, labelcolor=ink)
        for spine in ax.spines.values():
            spine.set_color(grid)
    fig.suptitle(title, color=ink)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="GuitarSet folder")
    parser.add_argument("--folds", type=int, nargs="+", default=list(range(N_PLAYERS)),
                        help="test player of each fold")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--tracks-per-group", type=int, default=1, help="tracks per (player, mode)")
    parser.add_argument("--selection-seed", type=int, default=0)
    parser.add_argument("--max-iter", type=int, default=500)
    parser.add_argument("--tol", type=float, default=1e-4)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if len(args.seeds) < 2 or len(args.folds) < 2:
        raise ValueError("at least two seeds and two folds are needed for a comparison")
    sample = training_sample(
        list_tracks(args.root), None, args.tracks_per_group, np.random.default_rng(args.selection_seed),
    )
    config = {
        "data": "GuitarSet 1.1.0, audio_mono-mic, data/README.md",
        "preprocessing": {
            "sample_rate": SAMPLE_RATE, "n_win": N_WIN, "hop": HOP, "f_max": F_MAX,
            "magnitude": "STFT magnitude, no level normalization",
        },
        "learner": "stand-in for gitara.templates.learn_templates: masked_start + fit",
        "init": "W0 uniform(0.5, 1.5) on labelled pitches and background, H0 = mask",
        "background": True,
        "objectives": list(OBJECTIVES),
        "max_iter": args.max_iter,
        "tol": args.tol,
        "eps": 1e-12,
        "normalize": True,
        "folds": args.folds,
        "tracks_per_group": args.tracks_per_group,
        "selection_seed": args.selection_seed,
        "excluded": list(SHIFTED_TRACKS),
        "tracks": [track.track_id for track in sample],
        "init_seeds": args.seeds,
    }
    record = start_run(
        "template_stability", config, seeds=sorted({*args.seeds, args.selection_seed}),
        manifest=DEFAULT_MANIFEST,
    )
    run_dir = Path(record["dir"])
    try:
        results = _experiment(args, sample, run_dir)
    except Exception as error:
        finish_run(record, "failed", errors=[repr(error)])
        raise
    finish_run(record, "ok", results)
    print(f"Zapis pokretanja: {run_dir}")


def _experiment(args: argparse.Namespace, sample: Sequence[Track], run_dir: Path) -> dict[str, Any]:
    data = {track.track_id: spectrogram_and_roll(track) for track in sample}
    templates: dict[str, NDArray] = {}
    results: dict[str, Any] = {}
    summary: dict[str, dict[str, Any]] = {}
    for objective in OBJECTIVES:
        Ws: dict[tuple[int, int], NDArray] = {}
        runs = []
        for fold in args.folds:
            train = fold_tracks(sample, fold)
            blocks = [data[track.track_id][0] for track in train]
            rolls = [data[track.track_id][1] for track in train]
            for seed in args.seeds:
                start = time.perf_counter()
                W, n_iter = learn_masked(blocks, rolls, objective=objective, seed=seed,
                                         max_iter=args.max_iter, tol=args.tol)
                seconds = time.perf_counter() - start
                Ws[fold, seed] = templates[f"{objective}_fold{fold}_seed{seed}"] = W
                runs.append({"fold": fold, "seed": seed, "n_iter": n_iter, "seconds": seconds})
                print(f"{objective:>9} fold={fold} seed={seed}  {n_iter} it  {seconds:.1f} s", flush=True)

        across_seeds = {fold: pairwise_similarity([Ws[fold, s] for s in args.seeds]) for fold in args.folds}
        across_folds = {seed: pairwise_similarity([Ws[f, seed] for f in args.folds]) for seed in args.seeds}
        with warnings.catch_warnings():  # pitches without any value stay NaN
            warnings.simplefilter("ignore", RuntimeWarning)
            seeds_median = np.nanmedian(np.array([mean for mean, _ in across_seeds.values()]), axis=0)
        results[objective] = {
            "runs": runs,
            "across_seeds": {str(f): {"mean": _json_values(m), "min": _json_values(s)}
                             for f, (m, s) in across_seeds.items()},
            "across_folds": {str(s): {"mean": _json_values(m), "min": _json_values(n)}
                             for s, (m, n) in across_folds.items()},
        }
        summary[objective] = {
            "across_seeds_median": _json_values(seeds_median),
            "across_folds_first_seed": _json_values(across_folds[args.seeds[0]][0]),
        }
        results[objective]["summary"] = summary[objective]
    results["columns"] = [*map(int, PITCHES), "background"]
    np.savez_compressed(run_dir / "templates.npz", **templates)
    plot(summary, f"Predlošci s maskom: {len(args.folds)} foldova, {len(args.seeds)} sjemena",
         run_dir / "template_stability.png")
    return results


if __name__ == "__main__":
    main()
