import unittest

import numpy as np

from gitara import templates

M_BINS, K = 20, 4  # the last pitch never sounds in the synthetic data
COMBS = {0: (2, 4, 6, 8), 1: (3, 6, 9, 12), 2: (5, 10, 15)}


def true_templates() -> np.ndarray:
    W = np.zeros((M_BINS, K))
    for k, bins in COMBS.items():
        for h, b in enumerate(bins):
            W[b, k] = 1.0 / (h + 1)
    return W


def synthetic_block(seed: int, n: int = 40, solo_only: bool = False):
    """A = W* H* with H* supported exactly on the roll; every frame has an active pitch."""
    rng = np.random.default_rng(seed)
    R = np.zeros((K, n), dtype=bool)
    for t in range(n):
        count = 1 if solo_only else rng.integers(1, 3)
        R[rng.choice(3, size=count, replace=False), t] = True
    H = np.where(R, rng.uniform(0.5, 2.0, size=R.shape), 0.0)
    return true_templates() @ H, R


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


class MaskTests(unittest.TestCase):
    def test_background_row_is_always_active(self) -> None:
        R = np.array([[1, 0, 1], [0, 0, 1]], dtype=bool)
        M = templates.mask_from_roll(R)
        self.assertEqual(M.shape, (3, 3))
        np.testing.assert_array_equal(M[:2], R)
        self.assertTrue(M[2].all())

    def test_without_background_is_a_copy(self) -> None:
        R = np.array([[1, 0], [0, 1]], dtype=bool)
        M = templates.mask_from_roll(R, background=False)
        np.testing.assert_array_equal(M, R)
        M[0, 0] = False
        self.assertTrue(R[0, 0])

    def test_invalid_roll_raises(self) -> None:
        for bad in (np.ones(3), np.array([[0.5, 1.0]]), np.array([[np.nan, 1.0]])):
            with self.assertRaises(ValueError):
                templates.mask_from_roll(bad)


class AverageTemplatesTests(unittest.TestCase):
    def test_recovers_normalized_templates_and_detects_inactive_pitch(self) -> None:
        blocks = [synthetic_block(0, solo_only=True), synthetic_block(1)]
        result = templates.average_templates(blocks)
        self.assertEqual(result.W.shape, (M_BINS, K))
        self.assertEqual(result.inactive, (3,))
        self.assertTrue((result.W[:, 3] == 0).all())
        expected = true_templates()[:, :3]
        expected = expected / expected.sum(axis=0)
        np.testing.assert_allclose(result.W[:, :3], expected, atol=1e-12)

    def test_pitch_that_only_sounds_in_chords_is_inactive(self) -> None:
        W = true_templates()
        R = np.zeros((K, 6), dtype=bool)
        R[0, :3] = True
        R[1, 3:] = True
        R[2, 4:] = True  # pitch 2 never sounds alone (frame 3 is pitch 1 only)
        H = R.astype(float)
        result = templates.average_templates([(W @ H, R)])
        self.assertEqual(result.inactive, (2, 3))

    def test_ignores_silent_and_empty_frames(self) -> None:
        W = true_templates()
        R = np.zeros((K, 4), dtype=bool)
        R[0, 0] = R[0, 1] = True
        A = W @ R.astype(float)
        A[:, 1] = 0.0  # labelled but zero energy
        result = templates.average_templates([(A, R)])
        expected = W[:, 0] / W[:, 0].sum()
        np.testing.assert_allclose(result.W[:, 0], expected)

    def test_columns_sum_to_one_for_active_pitches(self) -> None:
        result = templates.average_templates([synthetic_block(2, solo_only=True)])
        sums = result.W.sum(axis=0)
        for k in range(K):
            self.assertAlmostEqual(sums[k], 0.0 if k in result.inactive else 1.0)


class ValidationTests(unittest.TestCase):
    def test_invalid_blocks_raise_value_error(self) -> None:
        A, R = synthetic_block(0)
        bad_blocks = [
            [],
            [(A,)],
            [(A[:, :-1], R)],
            [(-A, R)],
            [(np.where(A > 0, np.nan, A), R)],
            [(A, R), (A[:-1], R)],
            [(A, R), (A, R[:-1])],
        ]
        for blocks in bad_blocks:
            with self.subTest(blocks=len(blocks)):
                with self.assertRaises(ValueError):
                    templates.average_templates(blocks)
                with self.assertRaises(ValueError):
                    templates.learn_templates(blocks)

    def test_unknown_objective_and_unlabelled_data_raise(self) -> None:
        A, R = synthetic_block(0)
        with self.assertRaises(ValueError):
            templates.learn_templates([(A, R)], objective="itakura-saito")
        with self.assertRaises(ValueError):
            templates.learn_templates([(A, np.zeros_like(R))])

    def test_kl_without_background_rejects_uncovered_frames(self) -> None:
        A, R = synthetic_block(0)
        R = R.copy()
        R[:, 5] = False  # frame 5 has energy but no label
        with self.assertRaisesRegex(ValueError, "1 frames"):
            templates.learn_templates([(A, R)], objective="kl", background=False)


class LearnTemplatesTests(unittest.TestCase):
    def fit(self, **kwargs) -> templates.Templates:
        blocks = [synthetic_block(0), synthetic_block(1)]
        params = dict(max_iter=500, tol=1e-9, seed=0, background=False)
        params.update(kwargs)
        return templates.learn_templates(blocks, **params)

    def test_learned_templates_match_true_templates_up_to_scale(self) -> None:
        # The mask fixes the permutation; scale is removed by comparing cosines.
        W_true = true_templates()
        for objective in ("kl", "frobenius"):
            with self.subTest(objective=objective):
                result = self.fit(objective=objective)
                self.assertEqual(result.W.shape, (M_BINS, K))
                for k in range(3):
                    self.assertGreater(cosine(result.W[:, k], W_true[:, k]), 0.95)

    def test_inactive_pitch_has_zero_column_and_is_reported(self) -> None:
        result = self.fit()
        self.assertEqual(result.inactive, (3,))
        self.assertTrue((result.W[:, 3] == 0).all())

    def test_output_is_finite_and_nonnegative(self) -> None:
        result = self.fit()
        self.assertTrue(np.isfinite(result.W).all() and (result.W >= 0).all())

    def test_objective_does_not_increase(self) -> None:
        for objective in ("kl", "frobenius"):
            with self.subTest(objective=objective):
                values = self.fit(objective=objective).objective
                self.assertGreater(len(values), 1)
                # data are fit exactly, so late values are float noise: compare to the initial value
                self.assertLessEqual(np.max(np.diff(values)), 1e-9 * values[0])

    def test_background_adds_a_last_column(self) -> None:
        result = self.fit(background=True)
        self.assertEqual(result.W.shape, (M_BINS, K + 1))
        self.assertEqual(result.inactive, (3,))

    def test_same_seed_gives_same_result(self) -> None:
        np.testing.assert_array_equal(self.fit(seed=3).W, self.fit(seed=3).W)


if __name__ == "__main__":
    unittest.main()
