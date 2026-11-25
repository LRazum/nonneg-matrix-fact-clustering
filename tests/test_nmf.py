import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from gitara.nmf import fit, frobenius, gradients, kl_divergence, stationarity


class ObjectiveTests(unittest.TestCase):
    def test_kl_zero_support_and_known_values(self) -> None:
        A = [[0, 2], [1, 0]]
        V = [[3, 1], [2, 0]]
        self.assertAlmostEqual(kl_divergence(A, V), 3 + math.log(2))
        self.assertEqual(kl_divergence(A, A), 0)
        self.assertEqual(kl_divergence([[1]], [[0]]), math.inf)

    def test_kl_nearly_equal_and_extreme_ratios(self) -> None:
        # D(1+t || 1) is asymptotic to t²/2.
        t = np.nextafter(1.0, 2.0) - 1
        self.assertAlmostEqual(kl_divergence([[1 + t]], [[1]]) / t**2, 0.5)
        # a/v would overflow, but log(a) - log(v) is finite.
        self.assertTrue(math.isfinite(kl_divergence([[1e100]], [[1e-300]])))
        rng = np.random.default_rng(73)
        for _ in range(8):
            self.assertGreaterEqual(kl_divergence(rng.random((5, 4)), rng.random((5, 4))), 0)

    def test_frobenius_is_half_the_squared_norm(self) -> None:
        self.assertEqual(frobenius([[0, 2], [1, 0]], [[3, 1], [2, 0]]), 5.5)

    def test_objectives_reject_bad_inputs(self) -> None:
        for loss in (kl_divergence, frobenius):
            for V in ([[1, 2]], [[float("nan")]], [[-1]], [[1j]], [1]):
                with self.subTest(loss=loss.__name__, V=V), self.assertRaises(ValueError):
                    loss([[1]], V)


class FitTests(unittest.TestCase):
    def test_kl_hand_calculated_iteration(self) -> None:
        A = np.array([[1, 3], [2, 4]])
        W0 = np.array([[1, 1], [1, 2]])
        H0 = np.ones((2, 2))
        expected_H = [[7 / 12, 17 / 12], [11 / 18, 25 / 18]]

        fixed = fit([A], W0, [H0], update_W=False, max_iter=1, eps=0)
        assert_array_equal(fixed.W, W0)
        assert_allclose(fixed.Hs[0], expected_H, rtol=1e-14, atol=0)

        learned = fit([A], W0, [H0], max_iter=1, eps=0, normalize=False)
        assert_allclose(learned.Hs[0], expected_H, rtol=1e-14, atol=0)
        assert_allclose(
            learned.W, [[4350 / 4343, 4336 / 4343], [9801 / 9815, 19644 / 9815]],
            rtol=1e-14, atol=0,
        )
        self.assertLess(learned.objective[-1], learned.objective[0])

    def test_frobenius_hand_calculated_iteration(self) -> None:
        result = fit(
            [[[1, 3], [2, 6]]], [[1], [1]], [[[1, 1]]],
            objective="frobenius", max_iter=1, eps=0, normalize=False,
        )
        assert_allclose(result.W, [[2 / 3], [4 / 3]], rtol=1e-14, atol=0)
        assert_allclose(result.Hs[0], [[1.5, 4.5]], rtol=1e-14, atol=0)
        self.assertEqual(result.objective[-1], 0)
        self.assertEqual(result.stop_reason, "zero_objective")

    def test_reconstructs_small_rank_two_matrix(self) -> None:
        true_W = np.array([[1, 0.2], [0.2, 1.2], [0.4, 0.5]])
        true_H = np.array([[1.3, 0.2, 1.2], [0.5, 1.9, 0.5]])
        A = true_W @ true_H
        W0 = [[0.8, 0.4], [0.4, 1.3], [0.6, 0.5]]
        H0 = [[1, 0.4, 1.3], [0.3, 1.8, 0.5]]
        for objective in ("kl", "frobenius"):
            with self.subTest(objective=objective):
                result = fit([A], W0, [H0], objective=objective, max_iter=600, eps=0, tol=0)
                assert_allclose(result.W @ result.Hs[0], A, rtol=1e-6, atol=1e-8)
                self.assertLess(result.objective[-1], 1e-12)

    def test_positive_seeded_cases_are_finite_nonnegative_and_nonincreasing(self) -> None:
        for seed in range(3):
            rng = np.random.default_rng(seed)
            blocks = [rng.uniform(0.1, 2, (6, n)) for n in (7, 5)]
            W0 = rng.uniform(0.2, 1, (6, 3))
            H0s = [rng.uniform(0.2, 1, (3, A.shape[1])) for A in blocks]
            for objective in ("kl", "frobenius"):
                with self.subTest(seed=seed, objective=objective):
                    result = fit(blocks, W0, H0s, objective=objective, max_iter=30, tol=0)
                    for factor in (result.W, *result.Hs):
                        self.assertTrue(np.isfinite(factor).all())
                        self.assertTrue((factor >= 0).all())
                    history = np.asarray(result.objective)
                    # Allow roundoff scaled by the size of the preceding objective.
                    self.assertTrue(np.all(np.diff(history) <= 1e-12 * history[:-1]))
                    self.assertEqual(len(history), result.n_iter + 1)

    def test_blocks_match_one_joined_block(self) -> None:
        A = np.array([[1, 3, 2], [2, 4, 1]])
        W0 = [[1, 1], [1, 2]]
        H0 = np.array([[1, 2, 1], [2, 1, 2]])
        for objective in ("kl", "frobenius"):
            with self.subTest(objective=objective):
                options = dict(objective=objective, max_iter=5, tol=0, eps=0)
                joined = fit([A], W0, [H0], **options)
                split = fit([A[:, :1], A[:, 1:]], W0, [H0[:, :1], H0[:, 1:]], **options)
                assert_allclose(split.W, joined.W, rtol=1e-12, atol=0)
                assert_allclose(np.concatenate(split.Hs, axis=1), joined.Hs[0], rtol=1e-12, atol=0)
                assert_allclose(split.objective, joined.objective, rtol=1e-12, atol=1e-14)

    def test_normalization_preserves_reconstruction_and_objective(self) -> None:
        A, W0, H0 = [[1, 3], [2, 4]], [[1, 1], [1, 2]], [[1, 1], [1, 1]]
        for objective in ("kl", "frobenius"):
            with self.subTest(objective=objective):
                options = dict(objective=objective, max_iter=1, eps=0)
                raw = fit([A], W0, [H0], normalize=False, **options)
                normalized = fit([A], W0, [H0], **options)
                assert_allclose(normalized.W.sum(axis=0), [1, 1])
                assert_allclose(normalized.W @ normalized.Hs[0], raw.W @ raw.Hs[0])
                assert_allclose(normalized.objective, raw.objective)

    def test_zero_entries_and_inactive_indices_are_preserved(self) -> None:
        W0 = [[1, 1, 0, 2], [1, 2, 0, 1]]
        H0s = [
            np.array([[1, 1], [0, 0], [0, 0], [0, 0]]),
            np.array([[1], [1], [0], [0]]),
        ]
        for objective in ("kl", "frobenius"):
            with self.subTest(objective=objective):
                result = fit(
                    [[[1, 2], [2, 3]], [[2], [4]]], W0, H0s,
                    objective=objective, max_iter=4, eps=0,
                )
                self.assertEqual(result.inactive, (2, 3))
                assert_array_equal(result.W[:, 2], 0)
                for H0, H in zip(H0s, result.Hs, strict=True):
                    assert_array_equal(H[H0 == 0], 0)

    def test_fixed_h_is_unchanged_and_inputs_are_not_mutated(self) -> None:
        A = np.array([[1, 3], [2, 4]])
        W0 = np.array([[1.0, 1.0], [1.0, 2.0]])
        H0 = np.array([[1.0, 2.0], [3.0, 1.0]])
        fixed = fit([A], W0, [H0], update_H=False, max_iter=2)
        assert_array_equal(fixed.Hs[0], H0)
        self.assertLess(fixed.objective[-1], fixed.objective[0])
        fit([A], W0, [H0], max_iter=2)
        assert_array_equal(A, [[1, 3], [2, 4]])
        assert_array_equal(W0, [[1, 1], [1, 2]])
        assert_array_equal(H0, [[1, 2], [3, 1]])

    def test_supports_float32_read_only_memmap_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spectrogram.npy"
            np.save(path, np.array([[1, 3], [2, 4]], dtype=np.float32))
            A = np.load(path, mmap_mode="r")
            mapped = fit([A], [[1, 1], [1, 2]], [[[1, 1], [1, 1]]], max_iter=2)
            dense = fit([A.astype(np.float64)], [[1, 1], [1, 2]], [[[1, 1], [1, 1]]], max_iter=2)
            del A  # Windows cannot delete a file that is still memory-mapped.
            assert_allclose(mapped.W, dense.W)
            assert_allclose(mapped.Hs[0], dense.Hs[0])

    def test_stop_reasons_and_iteration_zero(self) -> None:
        zero = fit([[[0]]], [[0]], [[[0]]], eps=0)
        self.assertEqual((zero.n_iter, zero.stop_reason, zero.objective), (0, "zero_objective", (0,)))
        initial = fit([[[2]]], [[1]], [[[1]]], max_iter=0)
        self.assertEqual((initial.n_iter, initial.stop_reason), (0, "max_iter"))
        assert_array_equal(initial.Hs[0], [[1]])
        stalled = fit([[[1], [2]]], [[1], [1]], [[[1.5]]], update_W=False, eps=0)
        self.assertEqual((stalled.n_iter, stalled.stop_reason), (1, "tol"))
        increased = fit(
            [[[1]]], [[1]], [[[0.5]]], update_W=False, max_iter=2, tol=1, eps=2,
        )
        self.assertEqual((increased.n_iter, increased.stop_reason), (2, "max_iter"))
        self.assertGreater(increased.objective[-1], increased.objective[0])

    def test_invalid_matrices_and_shapes_raise_value_error(self) -> None:
        cases = [
            ([], [[1]], []),
            ([[[1]]], [[1]], []),
            ([[[1]]], np.zeros((1, 0)), [np.zeros((0, 1))]),
            ([[[1], [2]]], [[1]], [[[1]]]),
            ([[[1, 2]]], [[1]], [[[1]]]),
            ([[[-1]]], [[1]], [[[1]]]),
            ([[[1]]], [[float("nan")]], [[[1]]]),
            ([[[1]]], [[1]], [[[float("inf")]]]),
        ]
        for blocks, W0, H0s in cases:
            with self.subTest(blocks=blocks, W0=W0, H0s=H0s), self.assertRaises(ValueError):
                fit(blocks, W0, H0s)

    def test_invalid_options_raise_value_error(self) -> None:
        for options in (
            {"objective": "l1"}, {"max_iter": -1}, {"max_iter": 0.5},
            {"tol": math.nan}, {"eps": -1}, {"eps": math.inf}, {"update_W": "false"},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                fit([[[1]]], [[1]], [[[1]]], **options)

    def test_numerical_failures_are_reported(self) -> None:
        with self.assertRaisesRegex(FloatingPointError, "KL|kl"):
            fit([[[1]]], [[0]], [[[0]]])
        with self.assertRaises(FloatingPointError):
            fit([[[1]]], [[1e300]], [[[1e300]]], objective="frobenius")



def total_objective(objective: str, blocks, W, Hs) -> float:
    loss = kl_divergence if objective == "kl" else frobenius
    return sum(loss(A, W @ H) for A, H in zip(blocks, Hs, strict=True))


def central_differences(f, X: np.ndarray, step: float = 1e-6) -> np.ndarray:
    G = np.zeros_like(X)
    for index in np.ndindex(X.shape):
        E = np.zeros_like(X)
        E[index] = step
        G[index] = (f(X + E) - f(X - E)) / (2 * step)
    return G


class GradientTests(unittest.TestCase):
    def test_gradients_match_central_differences(self) -> None:
        rng = np.random.default_rng(11)
        blocks = [rng.uniform(0.1, 1, (4, 3)), rng.uniform(0.1, 1, (4, 2))]
        blocks[0][0, 0] = 0  # a zero datum follows the 0 log 0 convention
        W = rng.uniform(0.5, 1.5, (4, 2))
        Hs = [rng.uniform(0.5, 1.5, (2, 3)), rng.uniform(0.5, 1.5, (2, 2))]
        for objective in ("kl", "frobenius"):
            grad_w, grad_hs = gradients(blocks, W, Hs, objective=objective)
            with self.subTest(objective=objective, factor="W"):
                numeric = central_differences(lambda X: total_objective(objective, blocks, X, Hs), W)
                assert_allclose(grad_w, numeric, rtol=1e-6, atol=1e-8)
            for b, grad in enumerate(grad_hs):
                with self.subTest(objective=objective, factor=f"H{b}"):
                    def f(X, b=b):
                        return total_objective(objective, blocks, W, [X if i == b else H for i, H in enumerate(Hs)])
                    assert_allclose(grad, central_differences(f, Hs[b]), rtol=1e-6, atol=1e-8)

    def test_multiplicative_updates_are_scaled_gradient_steps(self) -> None:
        # KL: eta = H / (W^T 1) and W / (1 H^T); Frobenius: eta = H / (W^T W H) and W / (W H H^T).
        rng = np.random.default_rng(12)
        A, W, H = rng.random((5, 4)), rng.uniform(0.5, 1.5, (5, 2)), rng.uniform(0.5, 1.5, (2, 4))
        scales = {
            "kl": (lambda: W.sum(axis=0)[:, None], lambda: H.sum(axis=1)[None, :]),
            "frobenius": (lambda: W.T @ W @ H, lambda: W @ H @ H.T),
        }
        for objective, (h_scale, w_scale) in scales.items():
            with self.subTest(objective=objective):
                grad_w, (grad_h,) = gradients([A], W, [H], objective=objective)
                options = dict(objective=objective, max_iter=1, tol=0, eps=0, normalize=False)
                h_step = fit([A], W, [H], update_W=False, **options).Hs[0]
                w_step = fit([A], W, [H], update_H=False, **options).W
                assert_allclose(h_step, H - H / h_scale() * grad_h, rtol=1e-12)
                assert_allclose(w_step, W - W / w_scale() * grad_w, rtol=1e-12)

    def test_exact_factorization_is_stationary(self) -> None:
        rng = np.random.default_rng(13)
        W, Hs = rng.uniform(0.5, 1.5, (4, 2)), [rng.uniform(0.5, 1.5, (2, 3)), rng.uniform(0.5, 1.5, (2, 1))]
        blocks = [W @ H for H in Hs]
        for objective in ("kl", "frobenius"):
            self.assertEqual(stationarity(blocks, W, Hs, objective=objective), (0.0, 0.0))

    def test_frobenius_origin_is_stationary_but_not_a_minimum(self) -> None:
        A = np.array([[1.0, 2.0], [3.0, 1.0]])
        W, H = np.zeros((2, 1)), np.zeros((1, 2))
        self.assertEqual(stationarity([A], W, [H], objective="frobenius"), (0.0, 0.0))
        t = 1e-2
        self.assertLess(frobenius(A, (t * np.ones((2, 1))) @ (t * np.ones((1, 2)))), frobenius(A, W @ H))
        # The KL objective is infinite there: positive data at zero reconstruction.
        with self.assertRaisesRegex(FloatingPointError, "KL"):
            stationarity([A], W, [H], objective="kl")

    def test_stationarity_detects_a_non_kkt_point(self) -> None:
        A = np.array([[1.0, 2.0], [3.0, 1.0]])
        W, H = np.ones((2, 1)), np.ones((1, 2))
        for objective in ("kl", "frobenius"):
            w_residual, h_residual = stationarity([A], W, [H], objective=objective)
            self.assertGreater(min(w_residual, h_residual), 0)
        # A zero entry with a negative gradient violates the KKT conditions: min(0, g) = g.
        _, (grad_h,) = gradients([A], W, [np.array([[0.0, 1.0]])], objective="frobenius")
        self.assertLess(grad_h[0, 0], 0)
        self.assertAlmostEqual(
            stationarity([A], W, [np.array([[0.0, 1.0]])], objective="frobenius")[1],
            np.linalg.norm(np.minimum([[0.0, 1.0]], grad_h)),
        )

    def test_invalid_inputs_are_rejected(self) -> None:
        A, W, H = np.ones((2, 2)), np.ones((2, 1)), np.ones((1, 2))
        cases = [
            ([A], -W, [H], "kl"), ([A], W, [np.ones((1, 3))], "kl"), ([A], W, [], "kl"),
            ([A * np.nan], W, [H], "frobenius"), ([A], W, [H], "l2"),
        ]
        for blocks, W_, Hs, objective in cases:
            with self.subTest(objective=objective), self.assertRaises(ValueError):
                gradients(blocks, W_, Hs, objective=objective)


if __name__ == "__main__":
    unittest.main()
