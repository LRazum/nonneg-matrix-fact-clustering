"""Learning pitch templates W from labelled recordings.

Two options (the choice between them is decided in task Z2):
- ``learn_templates``: masked NMF. H is initialized with the piano-roll mask, so entries of
  H that start at zero stay zero (multiplicative updates keep zeros), and only the notes that
  actually sound in a frame can explain its spectrum.
- ``average_templates``: the template of a pitch is the mean of the l1-normalized spectra of
  frames in which only that pitch sounds.

Conventions follow docs/plan/PODJELA.md: columns of W follow the order of ``PITCHES``; a pitch
without labelled frames gets a zero column (and is listed in ``inactive``). With a background
component, W has one extra last column that transcription skips.

``blocks`` is a sequence of ``(A, R)`` pairs: spectrogram ``A`` of shape (m, n) and boolean
piano roll ``R`` of shape (K, n) for one recording.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gitara import nmf


@dataclass(frozen=True)
class Templates:
    W: np.ndarray  # (m, K) or (m, K + 1) with a background column last
    inactive: tuple[int, ...]  # pitch indices (< K) with a zero column
    objective: np.ndarray | None = None  # objective per iteration; None for averaging


def mask_from_roll(R: np.ndarray, background: bool = True) -> np.ndarray:
    """Mask M of shape (K, n), or (K + 1, n) with an always-active background row last."""
    R = np.asarray(R)
    if R.ndim != 2:
        raise ValueError(f"piano roll must be 2-D, got shape {R.shape}")
    if R.dtype != bool:
        if not np.isin(R, (0, 1)).all():
            raise ValueError("piano roll must contain only 0/1 values")
        R = R.astype(bool)
    if background:
        return np.vstack([R, np.ones((1, R.shape[1]), dtype=bool)])
    return R.copy()


def _check_blocks(blocks) -> tuple[list[tuple[np.ndarray, np.ndarray]], int, int]:
    blocks = list(blocks)
    if not blocks:
        raise ValueError("at least one block is required")
    checked: list[tuple[np.ndarray, np.ndarray]] = []
    m = K = None
    for i, block in enumerate(blocks):
        try:
            A, R = block
        except (TypeError, ValueError):
            raise ValueError(f"block {i} must be a (spectrogram, piano roll) pair") from None
        A = np.asarray(A, dtype=np.float64)
        R = mask_from_roll(R, background=False)
        if A.ndim != 2:
            raise ValueError(f"block {i}: spectrogram must be 2-D, got shape {A.shape}")
        if not np.isfinite(A).all() or (A < 0).any():
            raise ValueError(f"block {i}: spectrogram must be finite and nonnegative")
        if R.shape[1] != A.shape[1]:
            raise ValueError(f"block {i}: {A.shape[1]} frames but piano roll has {R.shape[1]}")
        if m is None:
            m, K = A.shape[0], R.shape[0]
        elif (A.shape[0], R.shape[0]) != (m, K):
            raise ValueError(f"block {i}: (bins, pitches) = {(A.shape[0], R.shape[0])}, expected {(m, K)}")
        checked.append((A, R))
    return checked, m, K


def average_templates(blocks) -> Templates:
    """Template of pitch k = mean l1-normalized spectrum of frames where only pitch k sounds.

    Frames with several notes, with no note, or with zero energy are ignored. Columns sum
    to 1; a pitch with no such frame is inactive (zero column).
    """
    checked, m, K = _check_blocks(blocks)
    total = np.zeros((m, K))
    count = np.zeros(K, dtype=np.int64)
    for A, R in checked:
        energy = A.sum(axis=0)
        use = (R.sum(axis=0) == 1) & (energy > 0)
        if not use.any():
            continue
        spectra = A[:, use] / energy[use]
        tones = R[:, use].argmax(axis=0)
        for k in range(K):
            chosen = tones == k
            total[:, k] += spectra[:, chosen].sum(axis=1)
            count[k] += chosen.sum()
    W = np.zeros((m, K))
    available = count > 0
    W[:, available] = total[:, available] / count[available]
    return Templates(W, tuple(int(k) for k in np.flatnonzero(~available)))


def learn_templates(
    blocks,
    objective: str = "kl",
    max_iter: int = 200,
    tol: float = 1e-4,
    seed: int = 0,
    background: bool = True,
) -> Templates:
    """Masked NMF over all blocks with a shared W (uses gitara.nmf.fit).

    W0 ~ Uniform(0.5, 1.5) from ``default_rng(seed)`` for pitches with at least one labelled
    frame and zero for the others; H0 is the mask (zeros stay zeros). Without a background
    component, KL needs every frame with energy to have at least one active pitch, otherwise
    the divergence is infinite; such frames raise ``ValueError`` instead of being dropped
    silently (choose a background component or select frames explicitly).
    """
    if objective not in ("kl", "frobenius"):
        raise ValueError(f"unknown objective {objective!r}")
    checked, m, K = _check_blocks(blocks)
    labelled = np.zeros(K, dtype=bool)
    for _, R in checked:
        labelled |= R.any(axis=1)
    if not labelled.any():
        raise ValueError("no pitch has a labelled frame")
    if objective == "kl" and not background:
        uncovered = sum(int(((A.sum(axis=0) > 0) & ~R.any(axis=0)).sum()) for A, R in checked)
        if uncovered:
            raise ValueError(
                f"{uncovered} frames with energy have no active pitch; KL would be infinite "
                "(use background=True or select training frames explicitly)"
            )

    rng = np.random.default_rng(seed)
    W0 = rng.uniform(0.5, 1.5, size=(m, K + int(background)))
    W0[:, :K][:, ~labelled] = 0.0
    H0s = [mask_from_roll(R, background).astype(np.float64) for _, R in checked]

    result = nmf.fit(
        [A for A, _ in checked], W0, H0s, objective=objective,
        update_W=True, update_H=True, max_iter=max_iter, tol=tol,
    )
    W = np.array(result.W, dtype=np.float64)
    inactive = tuple(k for k in range(K) if not W[:, k].any())
    return Templates(W, inactive, np.asarray(result.objective, dtype=np.float64))
