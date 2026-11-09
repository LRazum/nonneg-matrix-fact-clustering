"""Blockwise Lee–Seung multiplicative updates for nonnegative matrix factorization."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

Matrix = NDArray[np.float64]
Objective = Literal["kl", "frobenius"]
StopReason = Literal["tol", "max_iter", "zero_objective"]


@dataclass(frozen=True)
class NMFResult:
    """Factors, objective history (including iteration zero), and stopping information."""

    W: Matrix
    Hs: tuple[Matrix, ...]
    objective: tuple[float, ...]
    n_iter: int
    stop_reason: StopReason
    inactive: tuple[int, ...]


def _matrix(value: ArrayLike, name: str) -> NDArray:
    try:
        matrix = np.asarray(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a nonempty real matrix") from error
    if matrix.ndim != 2 or not matrix.size or matrix.dtype.kind not in "buif":
        raise ValueError(f"{name} must be a nonempty real matrix")
    if not np.isfinite(matrix).all() or np.any(matrix < 0):
        raise ValueError(f"{name} must contain finite nonnegative values")
    return matrix


def _objective_inputs(A: ArrayLike, V: ArrayLike) -> tuple[Matrix, Matrix]:
    data = _matrix(A, "A")
    reconstruction = _matrix(V, "V")
    if data.shape != reconstruction.shape:
        raise ValueError("A and V must have the same shape")
    return np.asarray(data, dtype=np.float64), np.asarray(reconstruction, dtype=np.float64)


def kl_divergence(A: ArrayLike, V: ArrayLike) -> float:
    """Return generalized KL divergence, with +inf for positive data at zero V."""
    with np.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
        return _kl_value(*_objective_inputs(A, V))


def frobenius(A: ArrayLike, V: ArrayLike) -> float:
    """Return half the squared Frobenius norm of A minus V."""
    with np.errstate(over="raise", invalid="raise", under="ignore"):
        return _frobenius_value(*_objective_inputs(A, V))


def _kl_value(A: Matrix, V: Matrix) -> float:
    positive = A > 0
    a, v = A[positive], V[positive]
    if np.any(v == 0):
        return np.inf

    difference = a - v
    near = np.abs(difference) <= 0.5 * v
    relative = difference[near] / v[near]
    near_loss = (1 + relative) * np.log1p(relative) - relative
    # The Taylor expansion avoids cancellation when a and v are nearly equal.
    small = np.abs(relative) < 1e-4
    t = relative[small]
    near_loss[small] = t**2 * (0.5 + t * (-1 / 6 + t / 12))

    a_far, v_far = a[~near], v[~near]
    far_loss = v_far + a_far * (np.log(a_far) - np.log(v_far) - 1)
    return float(V[~positive].sum() + (v[near] * near_loss).sum() + far_loss.sum())


def _frobenius_value(A: Matrix, V: Matrix) -> float:
    difference = A - V
    return float(np.sum((0.5 * difference) * difference))


def _kl_ratio(A: Matrix, V: Matrix, eps: float) -> Matrix:
    positive = A > 0
    if np.any(positive & (V == 0)):
        raise FloatingPointError("KL reconstruction is zero where the data are positive")
    return np.divide(A, np.maximum(V, eps), out=np.zeros_like(V), where=positive)


def _multiply_update(factor: Matrix, numerator: Matrix, denominator: Matrix, eps: float) -> None:
    # Preserve zeros and leave entries with 0/0 unchanged.
    update = (factor != 0) & ((numerator != 0) | (denominator != 0))
    ratio = np.divide(
        numerator, np.maximum(denominator, eps), out=np.ones_like(factor), where=update,
    )
    factor *= ratio


def _update_h(
    blocks: tuple[NDArray, ...], W: Matrix, Hs: tuple[Matrix, ...],
    objective: Objective, eps: float,
) -> None:
    if objective == "kl":
        denominator = W.sum(axis=0)[:, None]
        for block, H in zip(blocks, Hs, strict=True):
            A = np.asarray(block, dtype=np.float64)
            _multiply_update(H, W.T @ _kl_ratio(A, W @ H, eps), denominator, eps)
    else:
        gram = W.T @ W
        for block, H in zip(blocks, Hs, strict=True):
            A = np.asarray(block, dtype=np.float64)
            _multiply_update(H, W.T @ A, gram @ H, eps)


def _update_w(
    blocks: tuple[NDArray, ...], W: Matrix, Hs: tuple[Matrix, ...],
    objective: Objective, eps: float,
) -> None:
    numerator = np.zeros_like(W)
    rank = W.shape[1]
    if objective == "kl":
        denominator = np.zeros(rank)
        for block, H in zip(blocks, Hs, strict=True):
            A = np.asarray(block, dtype=np.float64)
            numerator += _kl_ratio(A, W @ H, eps) @ H.T
            denominator += H.sum(axis=1)
        _multiply_update(W, numerator, denominator[None, :], eps)
    else:
        gram = np.zeros((rank, rank))
        for block, H in zip(blocks, Hs, strict=True):
            A = np.asarray(block, dtype=np.float64)
            numerator += A @ H.T
            gram += H @ H.T
        _multiply_update(W, numerator, W @ gram, eps)


def _normalize(W: Matrix, Hs: tuple[Matrix, ...]) -> None:
    scales = W.sum(axis=0)
    scales[scales == 0] = 1
    W /= scales
    for H in Hs:
        H *= scales[:, None]


def _total_objective(
    blocks: tuple[NDArray, ...], W: Matrix, Hs: tuple[Matrix, ...], objective: Objective,
) -> float:
    loss = _kl_value if objective == "kl" else _frobenius_value
    total = 0.0
    for index, (block, H) in enumerate(zip(blocks, Hs, strict=True)):
        value = loss(np.asarray(block, dtype=np.float64), W @ H)
        if value == np.inf:
            raise FloatingPointError(f"Block {index}: KL reconstruction is zero where the data are positive")
        total += value
    if not np.isfinite(total):
        raise FloatingPointError(f"Nonfinite total {objective} objective")
    return total


def _nonnegative_option(value: float, name: str) -> float:
    if isinstance(value, Real) and not isinstance(value, bool):
        try:
            number = float(value)
        except OverflowError:
            pass
        else:
            if np.isfinite(number) and number >= 0:
                return number
    raise ValueError(f"{name} must be a finite nonnegative number")


def fit(
    blocks: Sequence[ArrayLike],
    W0: ArrayLike,
    H0s: Sequence[ArrayLike],
    *,
    objective: Objective = "kl",
    update_W: bool = True,
    update_H: bool = True,
    max_iter: int = 200,
    tol: float = 1e-4,
    eps: float = 1e-12,
    normalize: bool = True,
) -> NMFResult:
    """Factor nonnegative (m, n_b) blocks into a shared W and one H per block.

    The shapes of W0 and H0s determine the positive component count. Input
    factors are copied. Data blocks are read as float64 one at a time.

    Each iteration updates all free H blocks, then W if free. Normalization
    rescales only when both factors are free. Update denominators and the
    denominator of A/(WH) have a floor of eps. Use eps=0 for the unperturbed
    denominators. A zero datum contributes zero to A/(WH), 0/0 in an update
    multiplier contributes one, and zero factor entries stay zero. Positive
    data at zero reconstruction are outside the KL domain even with eps > 0.

    The objective history uses the actual reconstruction without eps. tol=0
    disables the relative-drop check. Increases stay in the history and do
    not satisfy that check. max_iter=0 evaluates the initial factors only.
    Invalid inputs raise ValueError and numerical failures raise FloatingPointError.
    """
    if not isinstance(objective, str) or objective not in ("kl", "frobenius"):
        raise ValueError("objective must be 'kl' or 'frobenius'")
    if isinstance(max_iter, (bool, np.bool_)) or not isinstance(max_iter, Integral) or max_iter < 0:
        raise ValueError("max_iter must be a nonnegative integer")
    tol = _nonnegative_option(tol, "tol")
    eps = _nonnegative_option(eps, "eps")
    if not all(isinstance(flag, (bool, np.bool_)) for flag in (update_W, update_H, normalize)):
        raise ValueError("update_W, update_H and normalize must be boolean")

    try:
        inputs, initial_h = tuple(blocks), tuple(H0s)
    except TypeError as error:
        raise ValueError("blocks and H0s must be sequences of matrices") from error
    if not inputs or len(inputs) != len(initial_h):
        raise ValueError("blocks and H0s must contain the same positive number of matrices")

    initial_w = _matrix(W0, "W0")
    m, rank = initial_w.shape
    data_blocks = tuple(_matrix(block, f"blocks[{i}]") for i, block in enumerate(inputs))
    h_blocks = tuple(_matrix(H, f"H0s[{i}]") for i, H in enumerate(initial_h))
    for i, (A, H) in enumerate(zip(data_blocks, h_blocks, strict=True)):
        if A.shape[0] != m or H.shape != (rank, A.shape[1]):
            raise ValueError(f"Incompatible W0, blocks[{i}] and H0s[{i}] shapes")

    with np.errstate(over="raise", divide="raise", invalid="raise", under="ignore"):
        W = np.array(initial_w, dtype=np.float64, copy=True)
        Hs = tuple(np.array(H, dtype=np.float64, copy=True) for H in h_blocks)
        history = [_total_objective(data_blocks, W, Hs, objective)]
        stop_reason: StopReason = "max_iter"
        for _ in range(max_iter):
            previous = history[-1]
            if previous == 0:
                break
            if update_H:
                _update_h(data_blocks, W, Hs, objective, eps)
            if update_W:
                _update_w(data_blocks, W, Hs, objective, eps)
            if normalize and update_W and update_H:
                _normalize(W, Hs)
            current = _total_objective(data_blocks, W, Hs, objective)
            history.append(current)
            if current <= previous and (previous - current) / previous < tol:
                stop_reason = "tol"
                break

    if history[-1] == 0:
        stop_reason = "zero_objective"
    used = np.zeros(rank, dtype=bool)
    for H in Hs:
        used |= np.any(H > 0, axis=1)
    inactive = tuple(np.flatnonzero(~used | ~np.any(W > 0, axis=0)).tolist())
    return NMFResult(W, Hs, tuple(history), len(history) - 1, stop_reason, inactive)
