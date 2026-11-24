"""Magnitude spectrogram, pitch conversions and piano roll.

The spectrogram ``A`` has frequency bins in rows and frames in columns, so that the model is
``A ≈ W H`` with spectral templates in the columns of ``W`` and activations in the rows of ``H``.
Each frame is centred: the signal is padded with ``n_win // 2`` zeros on both sides, and frame
``t`` is centred on sample ``t * hop``, i.e. at time ``times[t] = t * hop / sr``.
"""

from __future__ import annotations

import warnings

import numpy as np

SAMPLE_RATE = 22_050  # uzoraka u sekundi
N_WIN = 2048  # duljina prozora N 
HOP = 512  # korak h između susjednih okvira
F_MAX = 5_500.0  # gornja granica frekvencije, binovi iznad toga se odbacuju

# MIDI E2 (open low E string) to E6. Proposed range; to be confirmed from the annotations in A4.
PITCHES = np.arange(40, 89)


def hann(n_win: int) -> np.ndarray:
    """Periodic Hann window ``w[n] = 0.5 - 0.5 cos(2 pi n / N)``, ``n = 0, ..., N - 1``."""
    n = np.arange(n_win)
    return 0.5 - 0.5 * np.cos(2 * np.pi * n / n_win)


def stft_magnitude(
    y: np.ndarray,
    sr: int = SAMPLE_RATE,
    n_win: int = N_WIN,
    hop: int = HOP,
    f_max: float = F_MAX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(A, freqs, times)`` for the mono signal ``y`` sampled at ``sr`` Hz.

    ``A[k, t] = |sum_n w[n] y_pad[t * hop + n] exp(-2 pi i k n / n_win)|`` for the bins
    ``k`` whose frequency ``k * sr / n_win`` is at most ``f_max``. ``A`` has shape ``(m, n)``,
    ``freqs`` shape ``(m,)`` in Hz and ``times`` shape ``(n,)`` in seconds. There are
    ``n = 1 + (len(y) - 1) // hop`` frames, so every frame centre lies inside the signal.
    The magnitude is not normalized: a sine of amplitude ``a`` exactly at a bin frequency gives
    ``a * sum(w) / 2`` in that bin.
    """
    y = np.asarray(y, dtype=np.float64)
    if y.ndim != 1 or y.size == 0:
        raise ValueError(f"y must be a non-empty 1-D signal, got shape {y.shape}")
    if not np.all(np.isfinite(y)):
        raise ValueError("y contains NaN or infinite samples")
    for label, value in (("sr", sr), ("n_win", n_win), ("hop", hop)):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer, got {value!r}")
    if n_win % 2:
        raise ValueError(f"n_win must be even so that frames are centred, got {n_win}")
    if hop > n_win:
        raise ValueError(f"hop ({hop}) must not exceed n_win ({n_win})")
    if not 0 < f_max <= sr / 2:
        raise ValueError(f"f_max must lie in (0, sr / 2] = (0, {sr / 2}], got {f_max!r}")

    n_frames = 1 + (y.size - 1) // hop
    padded = np.pad(y, n_win // 2)
    frames = np.lib.stride_tricks.sliding_window_view(padded, n_win)[::hop][:n_frames]
    spectrum = np.abs(np.fft.rfft(frames * hann(n_win), axis=1)).T

    freqs = np.fft.rfftfreq(n_win, d=1 / sr)
    keep = freqs <= f_max
    times = np.arange(n_frames) * hop / sr
    return spectrum[keep], freqs[keep], times


def midi_to_hz(pitch):
    """Frequency in Hz of a MIDI pitch: ``440 * 2 ** ((pitch - 69) / 12)``."""
    return 440.0 * 2.0 ** ((np.asarray(pitch, dtype=np.float64) - 69) / 12)


def hz_to_midi(frequency):
    """MIDI pitch of a positive frequency in Hz: ``69 + 12 * log2(frequency / 440)``."""
    frequency = np.asarray(frequency, dtype=np.float64)
    if not np.all(np.isfinite(frequency)) or np.any(frequency <= 0):
        raise ValueError("frequencies must be positive and finite")
    return 69 + 12 * np.log2(frequency / 440.0)


def piano_roll(
    intervals: np.ndarray,
    pitches: np.ndarray,
    times: np.ndarray,
    pitch_set: np.ndarray = PITCHES,
) -> np.ndarray:
    """Return the ``bool`` piano roll ``R`` of shape ``(K, n)`` for ``K = len(pitch_set)``.

    ``R[k, t]`` is true if some note has rounded pitch ``pitch_set[k]`` and
    ``onset <= times[t] < offset``. Pitches are rounded to the nearest integer, halves up.
    Notes whose rounded pitch is not in ``pitch_set`` are left out of ``R``, and a
    ``UserWarning`` reports how many there are.
    """
    intervals = np.asarray(intervals, dtype=np.float64)
    if intervals.size == 0:
        intervals = intervals.reshape(0, 2)
    pitches = np.asarray(pitches, dtype=np.float64)
    times = np.asarray(times, dtype=np.float64)
    pitch_set = np.asarray(pitch_set)
    if intervals.ndim != 2 or intervals.shape[1] != 2 or pitches.shape != (len(intervals),):
        raise ValueError(
            f"intervals must have shape (N, 2) and pitches (N,), got {intervals.shape} "
            f"and {pitches.shape}"
        )
    if not (np.all(np.isfinite(intervals)) and np.all(np.isfinite(pitches))):
        raise ValueError("note intervals and pitches must be finite")
    if np.any(intervals[:, 1] <= intervals[:, 0]):
        raise ValueError("every note must end after it starts")
    if times.ndim != 1 or not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0):
        raise ValueError("times must be a finite, strictly increasing 1-D array")
    if (
        pitch_set.ndim != 1
        or not np.issubdtype(pitch_set.dtype, np.integer)
        or np.any(np.diff(pitch_set) <= 0)
    ):
        raise ValueError("pitch_set must be a strictly increasing 1-D array of integers")

    rounded = np.floor(pitches + 0.5).astype(np.int64)
    rows = np.searchsorted(pitch_set, rounded)
    found = pitch_set[np.minimum(rows, len(pitch_set) - 1)]
    inside = (rows < len(pitch_set)) & (found == rounded)
    outside = int(np.count_nonzero(~inside))
    if outside:
        warnings.warn(
            f"{outside} of {len(pitches)} notes have pitches outside "
            f"{pitch_set[0]}-{pitch_set[-1]} and are left out of the piano roll",
            UserWarning,
            stacklevel=2,
        )

    roll = np.zeros((len(pitch_set), len(times)), dtype=bool)
    first = np.searchsorted(times, intervals[:, 0], side="left")
    stop = np.searchsorted(times, intervals[:, 1], side="left")
    for row, start, end in zip(rows[inside], first[inside], stop[inside]):
        roll[row, start:end] = True
    return roll
