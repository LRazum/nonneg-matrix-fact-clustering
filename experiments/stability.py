"""B6, unsupervised part: non-uniqueness and distance to stationarity on one recording.

Run from the repository root, after ``uv run python -m gitara.data download``::

    uv run python -m experiments.stability

NMF of one training recording is run from several random starts for each objective. The
columns of every ``W`` are matched to those of the first start by the Hungarian method on
their cosine similarity (``scipy.optimize.linear_sum_assignment``). A matched similarity of 1
for every column would mean the same factorization up to permutation and scaling; lower
values, together with different final objective values, show that the starts reach different
factorizations of the same data.

The distance to stationarity (``gitara.nmf.stationarity``) is measured at the start and at the
end of every run, both at the normalization of ``fit`` (columns of ``W`` with unit l1 norm).
Non-increase of the objective is a theorem; a small final distance is only an observation.
The template stability across seeds and folds with the mask needs ``gitara.templates`` (C3)
and is not part of this script.

Outputs go to the provenance directory ``results/runs/<id>/``: ``run.json``,
``stability.png`` and ``activations.png``. The latter shows, for the first KL start, the
activations ``H`` with components ordered by the frequency of their largest template bin,
under the annotated piano roll of the same recording (for the first walkthrough, Z1).
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import linear_sum_assignment

from experiments.convergence import spectrogram_and_roll
from gitara.data import DEFAULT_MANIFEST, DEFAULT_ROOT, list_tracks
from gitara.nmf import fit, stationarity
from gitara.provenance import finish_run, start_run
from gitara.spectrogram import F_MAX, HOP, N_WIN, PITCHES, SAMPLE_RATE

OBJECTIVES = ("kl", "frobenius")


def cosine_matrix(X: NDArray, Y: NDArray) -> NDArray[np.float64]:
    """Cosine similarity of every column of X with every column of Y; zero columns give 0."""
    def unit(M: NDArray) -> NDArray[np.float64]:
        M = np.asarray(M, dtype=np.float64)
        norms = np.linalg.norm(M, axis=0)
        return np.divide(M, norms, out=np.zeros_like(M), where=norms > 0)

    return unit(X).T @ unit(Y)


def match_components(reference: NDArray, other: NDArray) -> tuple[NDArray[np.intp], NDArray[np.float64]]:
    """Return ``(order, similarity)`` with ``other[:, order[k]]`` matched to ``reference[:, k]``.

    The matching maximizes the total cosine similarity (Hungarian method); ``similarity[k]``
    is the cosine similarity of the k-th matched pair.
    """
    similarity = cosine_matrix(reference, other)
    rows, order = linear_sum_assignment(similarity, maximize=True)
    return order[np.argsort(rows)], similarity[rows, order][np.argsort(rows)]


def normalized(W: NDArray, Hs: Sequence[NDArray]) -> tuple[NDArray[np.float64], list[NDArray[np.float64]]]:
    """Rescale to unit l1 columns of W, as ``fit`` does, keeping every W H_b."""
    scales = np.asarray(W, dtype=np.float64).sum(axis=0)
    scales[scales == 0] = 1
    return W / scales, [H * scales[:, None] for H in Hs]


def run_starts(
    A: NDArray, rank: int, seeds: Sequence[int], objective: str, max_iter: int, tol: float,
) -> list[dict[str, Any]]:
    """Fit from each seed and record the factors, objective and stationarity at start and end."""
    m, n = A.shape
    runs = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        W0, H0 = rng.uniform(0.5, 1.5, (m, rank)), rng.uniform(0.5, 1.5, (rank, n))
        result = fit([A], W0, [H0], objective=objective, max_iter=max_iter, tol=tol)
        start = stationarity([A], *normalized(W0, [H0]), objective=objective)
        end = stationarity([A], result.W, result.Hs, objective=objective)
        runs.append({
            "seed": seed, "W": result.W, "H": result.Hs[0],
            "n_iter": result.n_iter, "stop_reason": result.stop_reason,
            "initial": result.objective[0], "final": result.objective[-1],
            "stationarity_start": list(start), "stationarity_end": list(end),
        })
    return runs


def compare_to_first(runs: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Matched and unmatched (same index) cosine similarities of each run to the first."""
    reference = runs[0]["W"]
    rows = []
    for run in runs[1:]:
        _, matched = match_components(reference, run["W"])
        same_index = np.diag(cosine_matrix(reference, run["W"]))
        rows.append({
            "seed": run["seed"],
            "matched": np.sort(matched).tolist(),
            "same_index_mean": float(same_index.mean()),
            "matched_mean": float(matched.mean()),
            "matched_min": float(matched.min()),
            "matched_above_0.99": int(np.count_nonzero(matched > 0.99)),
        })
    return rows


def plot(comparisons: dict[str, list[dict[str, Any]]], title: str, path: Path) -> None:
    """Sorted matched similarities to the first start, one panel per objective."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid, color = "#0b0b0b", "#898781", "#e1e0d9", "#2a78d6"
    fig, axes = plt.subplots(1, len(comparisons), figsize=(5 * len(comparisons), 3.6), squeeze=False)
    fig.patch.set_facecolor("#fcfcfb")
    for ax, (objective, rows) in zip(axes[0], comparisons.items()):
        for row in rows:
            ranks = np.arange(1, len(row["matched"]) + 1)
            ax.plot(ranks, row["matched"], color=color, linewidth=2, alpha=0.6)
        mean_same = np.mean([row["same_index_mean"] for row in rows])
        ax.axhline(mean_same, color=muted, linewidth=1, linestyle="--")
        ax.annotate("bez sparivanja (prosjek)", (1, mean_same), xycoords=("axes fraction", "data"),
                    xytext=(-4, 4), textcoords="offset points", ha="right", color=muted, fontsize=8)
        ax.set_title("KL" if objective == "kl" else "Frobenius", color=ink)
        ax.set_xlabel("sparene komponente, poredane po sličnosti")
        ax.set_ylabel("kosinusna sličnost s prvim sjemenom")
        ax.set_ylim(0, 1.02)
        ax.set_facecolor("#fcfcfb")
        ax.grid(color=grid, linewidth=0.8)
        ax.tick_params(colors=muted, labelcolor=ink)
        for spine in ax.spines.values():
            spine.set_color(grid)
    fig.suptitle(title, color=ink)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_activations(W: NDArray, H: NDArray, roll: NDArray, title: str, path: Path) -> None:
    """Piano roll above the activations in dB, rows ordered by the peak bin of each template."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid = "#0b0b0b", "#898781", "#e1e0d9"
    order = np.argsort(np.argmax(W, axis=0), kind="stable")
    end = H.shape[1] * HOP / SAMPLE_RATE
    floor = 1e-4 * H.max()  # 80 dB below the largest activation
    H_db = 20 * np.log10(np.maximum(H[order], floor) / H.max())
    fig, (top, bottom) = plt.subplots(2, 1, sharex=True, figsize=(10, 6.5))
    fig.patch.set_facecolor("#fcfcfb")
    top.imshow(roll, aspect="auto", origin="lower", cmap="Greys", interpolation="nearest",
               extent=(0, end, PITCHES[0] - 0.5, PITCHES[-1] + 0.5))
    top.set_ylabel("MIDI visina (anotacija)")
    image = bottom.imshow(H_db, aspect="auto", origin="lower", cmap="Blues", interpolation="nearest",
                          extent=(0, end, -0.5, H.shape[0] - 0.5), vmin=-80, vmax=0)
    bottom.set_ylabel("komponenta, po vršnoj frekvenciji")
    bottom.set_xlabel("vrijeme (s)")
    colorbar = fig.colorbar(image, ax=[top, bottom], shrink=0.5, label="aktivacija (dB)")
    colorbar.ax.tick_params(colors=muted, labelcolor=ink)
    for ax in (top, bottom):
        ax.tick_params(colors=muted, labelcolor=ink)
        for spine in ax.spines.values():
            spine.set_color(grid)
    fig.suptitle(title, color=ink)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="GuitarSet folder")
    parser.add_argument("--held-out-player", type=int, default=5, help="never loaded")
    parser.add_argument("--track", default="00_BN1-129-Eb_comp")
    parser.add_argument("--rank", type=int, default=len(PITCHES))
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--max-iter", type=int, default=1000)
    parser.add_argument("--tol", type=float, default=1e-4)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if len(args.seeds) < 2:
        raise ValueError("at least two seeds are needed for a comparison")
    track = {track.track_id: track for track in list_tracks(args.root)}[args.track]
    if track.player == args.held_out_player:
        raise ValueError(f"{track.track_id} belongs to the held-out player")
    config = {
        "data": "GuitarSet 1.1.0, audio_mono-mic, data/README.md",
        "preprocessing": {
            "sample_rate": SAMPLE_RATE, "n_win": N_WIN, "hop": HOP, "f_max": F_MAX,
            "magnitude": "STFT magnitude, no level normalization",
        },
        "held_out_player": args.held_out_player,
        "track": track.track_id,
        "rank": args.rank,
        "init": "W0, H0 uniform(0.5, 1.5)",
        "objectives": list(OBJECTIVES),
        "max_iter": args.max_iter,
        "tol": args.tol,
        "eps": 1e-12,
        "normalize": True,
        "matching": "Hungarian on cosine similarity of W columns, reference = first seed",
    }
    record = start_run("stability", config, seeds=args.seeds, manifest=DEFAULT_MANIFEST)
    run_dir = Path(record["dir"])
    try:
        A, roll = spectrogram_and_roll(track)
        results, comparisons = {}, {}
        for objective in OBJECTIVES:
            runs = run_starts(A, args.rank, args.seeds, objective, args.max_iter, args.tol)
            comparisons[objective] = compare_to_first(runs)
            results[objective] = {
                "runs": [{key: value for key, value in run.items() if key not in ("W", "H")} for run in runs],
                "comparisons": comparisons[objective],
            }
            if objective == "kl":
                plot_activations(runs[0]["W"], runs[0]["H"], roll,
                                 f"KL bez nadzora: {track.track_id}, r = {args.rank}, sjeme {runs[0]['seed']}",
                                 run_dir / "activations.png")
            for run in runs:
                print(f"{objective:>9} seed={run['seed']}  {run['n_iter']} it  final {run['final']:.6g}  "
                      f"stationarity {run['stationarity_start']} -> {run['stationarity_end']}", flush=True)
        plot(comparisons, f"Bez nadzora: {track.track_id}, r = {args.rank}, {len(args.seeds)} sjemena",
             run_dir / "stability.png")
    except Exception as error:
        finish_run(record, "failed", errors=[repr(error)])
        raise
    finish_run(record, "ok", results)
    print(f"Zapis pokretanja: {run_dir}")


if __name__ == "__main__":
    main()
