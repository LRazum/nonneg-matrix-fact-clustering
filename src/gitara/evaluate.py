"""Note-level precision, recall and F1 by maximum bipartite matching.

An estimated note may match a reference note if their onsets differ by at most ``onset_tol``
seconds and their pitches by at most ``pitch_tol_cents`` cents. Offsets are not compared. Each
note is used at most once, so the number of true positives ``TP`` is the size of a maximum
matching in the bipartite graph of allowed pairs. This follows the onset-only note measure of
``mir_eval.transcription`` (Raffel et al., ISMIR 2014), which the tests use as a reference.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

ONSET_TOL = 0.05
PITCH_TOL_CENTS = 50.0
# Distances are rounded to this many decimals before comparison, as in mir_eval, so that a
# difference of exactly 50 ms or 50 cents is not lost to floating-point error.
DISTANCE_DECIMALS = 4


@dataclass(frozen=True)
class NoteScores:
    """Scores of one estimated transcription against its reference.

    ``precision`` is ``nan`` when there are no estimated notes and ``recall`` is ``nan`` when
    there are no reference notes; ``f1`` is then 0 by convention. ``matches`` holds the matched
    ``(reference index, estimate index)`` pairs, sorted by reference index.
    """

    precision: float
    recall: float
    f1: float
    tp: int
    n_ref: int
    n_est: int
    matches: np.ndarray


def note_scores(
    ref_intervals: np.ndarray,
    ref_pitches: np.ndarray,
    est_intervals: np.ndarray,
    est_pitches: np.ndarray,
    onset_tol: float = ONSET_TOL,
    pitch_tol_cents: float = PITCH_TOL_CENTS,
) -> NoteScores:
    """Return note-level precision, recall, F1 and true positives.

    Intervals have shape ``(N, 2)`` with onset and offset in seconds; pitches have shape
    ``(N,)`` in MIDI units, so one semitone is 100 cents. With ``TP`` matched pairs,
    ``P = TP / n_est``, ``R = TP / n_ref`` and ``F1 = 2 P R / (P + R)``, with ``F1 = 0`` when
    ``P + R = 0`` or when either is undefined.
    """
    ref_intervals, ref_pitches = _notes(ref_intervals, ref_pitches, "reference")
    est_intervals, est_pitches = _notes(est_intervals, est_pitches, "estimated")
    for label, value in (("onset_tol", onset_tol), ("pitch_tol_cents", pitch_tol_cents)):
        if not np.isfinite(value) or value < 0:
            raise ValueError(f"{label} must be a finite non-negative number, got {value!r}")

    n_ref, n_est = len(ref_pitches), len(est_pitches)
    onset_distance = np.abs(ref_intervals[:, :1] - est_intervals[:, 0])
    cent_distance = 100 * np.abs(ref_pitches[:, None] - est_pitches)
    allowed = (np.round(onset_distance, DISTANCE_DECIMALS) <= onset_tol) & (
        np.round(cent_distance, DISTANCE_DECIMALS) <= pitch_tol_cents
    )

    if allowed.any():
        est_of_ref = maximum_bipartite_matching(csr_matrix(allowed), perm_type="column")
        ref_index = np.flatnonzero(est_of_ref >= 0)
        matches = np.column_stack((ref_index, est_of_ref[ref_index]))
    else:
        matches = np.zeros((0, 2), dtype=np.int64)
    tp = len(matches)

    precision, recall, f1 = _precision_recall_f1(tp, n_ref, n_est)
    return NoteScores(precision, recall, f1, tp, n_ref, n_est, matches.astype(np.int64))


@dataclass(frozen=True)
class PooledScores:
    """Micro-averaged scores of several tracks: counts are summed before dividing."""

    precision: float
    recall: float
    f1: float
    tp: int
    n_ref: int
    n_est: int
    n_tracks: int


def pool_scores(scores: Iterable[NoteScores]) -> PooledScores:
    """Pool per-track scores into ``P = sum TP / sum n_est``, ``R = sum TP / sum n_ref``.

    Every note counts equally, so this is not the mean of the per-track F1 values. The
    project's main measure is this pooled F1 over the tracks of one test player.
    """
    scores = list(scores)
    if not scores:
        raise ValueError("pool_scores needs at least one track")
    tp = sum(score.tp for score in scores)
    n_ref = sum(score.n_ref for score in scores)
    n_est = sum(score.n_est for score in scores)
    precision, recall, f1 = _precision_recall_f1(tp, n_ref, n_est, stacklevel=3)
    return PooledScores(precision, recall, f1, tp, n_ref, n_est, len(scores))


def _precision_recall_f1(
    tp: int, n_ref: int, n_est: int, stacklevel: int = 3
) -> tuple[float, float, float]:
    if n_est == 0:
        warnings.warn(
            "no estimated notes: precision is undefined", UserWarning, stacklevel=stacklevel
        )
    if n_ref == 0:
        warnings.warn(
            "no reference notes: recall is undefined", UserWarning, stacklevel=stacklevel
        )
    precision = tp / n_est if n_est else float("nan")
    recall = tp / n_ref if n_ref else float("nan")
    f1 = 2 * precision * recall / (precision + recall) if tp else 0.0
    return precision, recall, f1


def _notes(intervals: np.ndarray, pitches: np.ndarray, label: str):
    intervals = np.asarray(intervals, dtype=np.float64)
    if intervals.size == 0:
        intervals = intervals.reshape(0, 2)
    pitches = np.asarray(pitches, dtype=np.float64)
    if intervals.ndim != 2 or intervals.shape[1] != 2 or pitches.shape != (len(intervals),):
        raise ValueError(
            f"{label} intervals must have shape (N, 2) and pitches (N,), "
            f"got {intervals.shape} and {pitches.shape}"
        )
    if not (np.all(np.isfinite(intervals)) and np.all(np.isfinite(pitches))):
        raise ValueError(f"{label} intervals and pitches must be finite")
    if np.any(intervals[:, 0] < 0):
        raise ValueError(f"{label} notes must not start before 0 s")
    if np.any(intervals[:, 1] <= intervals[:, 0]):
        raise ValueError(f"every {label} note must end after it starts")
    return intervals, pitches
