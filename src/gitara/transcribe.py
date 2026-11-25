"""Transcription with a fixed template matrix W: activations and notes from activations.

Conventions follow docs/plan/PODJELA.md (shared interfaces):
- rows of H and columns of W follow the order of ``PITCHES``; an inactive pitch has a
  zero column in W and a zero row in H;
- an optional background component, if used, is the last row of H and is ignored when
  notes are extracted;
- note onset is ``times`` of the first active frame, offset is ``times`` of the first
  following inactive frame (``times[-1] + frame_step`` if the run reaches the last frame).
"""
from __future__ import annotations

import numpy as np

from gitara import nmf


def activations(
    A: np.ndarray,
    W: np.ndarray,
    objective: str = "kl",
    max_iter: int = 200,
    tol: float = 1e-4,
) -> np.ndarray:
    """Solve min_{H>=0} D(A || W H) for fixed W with gitara.nmf.fit (update_W=False).

    ``W`` has shape (m, r); zero columns mark inactive components. The returned H has
    shape (r, n) with exactly zero rows for the inactive components.
    """
    A = np.asarray(A, dtype=np.float64)
    W = np.asarray(W, dtype=np.float64)
    if A.ndim != 2 or W.ndim != 2 or A.shape[0] != W.shape[0]:
        raise ValueError(f"incompatible shapes: A {A.shape}, W {W.shape}")
    if not (np.isfinite(A).all() and np.isfinite(W).all()):
        raise ValueError("A and W must contain only finite values")
    if (A < 0).any() or (W < 0).any():
        raise ValueError("A and W must be nonnegative")
    available = W.any(axis=0)
    if not available.any():
        raise ValueError("W has no active (nonzero) column")

    H0 = np.zeros((W.shape[1], A.shape[1]))
    H0[available] = 1.0
    result = nmf.fit(
        [A], W, [H0], objective=objective, update_W=False, update_H=True,
        max_iter=max_iter, tol=tol,
    )
    H = np.array(result.Hs[0], dtype=np.float64)
    H[~available] = 0.0
    return H


def extract_notes(
    H: np.ndarray,
    times: np.ndarray,
    pitches: np.ndarray,
    frame_step: float,
    threshold: float,
    min_duration: float,
    retrigger: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Turn activations into notes ``(intervals (N, 2), pitches (N,))``.

    1. Take the first K = len(pitches) rows (a background row is ignored) and divide them by
       their largest value over the whole recording; an all-zero H gives no notes.
    2. A frame is active if the normalized activation is >= ``threshold`` (0 < threshold <= 1).
    3. Each maximal run of active frames in a row becomes a note.
    4. If ``retrigger`` is given, a run is split before frame ``t`` when the rise
       ``d_t = h_t - h_{t-1}`` (of the normalized activation) exceeds ``retrigger``, is a local
       maximum of the rise (``d_t >= d_{t-1}`` and ``d_t > d_{t+1}``), AND the activation has
       stopped rising at least once since the last cut (``d_s <= 0`` for some ``s`` strictly
       between the last cut, or the start of the run, and ``t``). A single attack smeared over
       several frames by the analysis window is therefore never split, even if it lies entirely
       inside an active run; a new attack needs a pause or a fall in the activation before it.
    5. Notes shorter than ``min_duration`` seconds are dropped.
    Notes are sorted by onset, then by pitch.
    """
    H = np.asarray(H, dtype=np.float64)
    times = np.asarray(times, dtype=np.float64)
    pitches = np.asarray(pitches, dtype=np.float64)
    if H.ndim != 2:
        raise ValueError(f"H must be 2-D, got shape {H.shape}")
    if pitches.ndim != 1:
        raise ValueError(f"pitches must be 1-D, got shape {pitches.shape}")
    K, n = len(pitches), H.shape[1]
    if H.shape[0] < K:
        raise ValueError(f"H has {H.shape[0]} rows but there are {K} pitches")
    if times.shape != (n,):
        raise ValueError(f"times must have shape ({n},), got {times.shape}")
    if not (np.isfinite(H).all() and np.isfinite(times).all()):
        raise ValueError("H and times must contain only finite values")
    if (H < 0).any():
        raise ValueError("H must be nonnegative")
    if not frame_step > 0:
        raise ValueError("frame_step must be positive")
    if not 0 < threshold <= 1:
        raise ValueError("threshold must satisfy 0 < threshold <= 1")
    if min_duration < 0:
        raise ValueError("min_duration must be nonnegative")
    if retrigger is not None and not retrigger > 0:
        raise ValueError("retrigger must be positive or None")

    empty = (np.empty((0, 2)), np.empty(0))
    tones = H[:K]
    peak = tones.max() if tones.size else 0.0
    if peak == 0.0:
        return empty
    norm = tones / peak
    active = norm >= threshold

    onsets: list[float] = []
    offsets: list[float] = []
    notes_pitch: list[float] = []
    for k in range(K):
        rise = np.diff(norm[k], prepend=0.0)  # d_t; the frame before 0 counts as silent
        edges = np.diff(np.concatenate(([0], active[k].astype(np.int8), [0])))
        for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
            cuts = [start]
            if retrigger is not None and stop - start > 1:
                fell = False  # has d_s <= 0 occurred since the last cut?
                for t in range(start + 1, stop):
                    following = rise[t + 1] if t + 1 < n else -np.inf
                    if fell and rise[t] > retrigger and rise[t] >= rise[t - 1] and rise[t] > following:
                        cuts.append(t)
                        fell = False
                    elif rise[t] <= 0:
                        fell = True
            cuts.append(stop)
            for first, end in zip(cuts[:-1], cuts[1:]):
                t0 = times[first]
                t1 = times[end] if end < n else times[-1] + frame_step
                if t1 - t0 >= min_duration - 1e-12:
                    onsets.append(float(t0))
                    offsets.append(float(t1))
                    notes_pitch.append(float(pitches[k]))

    if not onsets:
        return empty
    intervals = np.column_stack([onsets, offsets])
    out_pitches = np.asarray(notes_pitch)
    order = np.lexsort((out_pitches, intervals[:, 0]))
    return intervals[order], out_pitches[order]
