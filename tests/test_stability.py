import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from experiments.stability import compare_to_first, cosine_matrix, match_components, pairwise, run_starts


class MatchingTests(unittest.TestCase):
    def test_permuted_and_scaled_columns_are_recovered(self) -> None:
        rng = np.random.default_rng(3)
        reference = rng.uniform(0, 1, (8, 5))
        permutation, scales = rng.permutation(5), rng.uniform(0.1, 10, 5)
        other = reference[:, permutation] * scales  # other[:, j] is reference[:, permutation[j]]
        order, similarity = match_components(reference, other)
        assert_array_equal(order, np.argsort(permutation))
        assert_allclose(similarity, 1)

    def test_matching_beats_any_fixed_order(self) -> None:
        rng = np.random.default_rng(4)
        X, Y = rng.random((6, 4)), rng.random((6, 4))
        _, similarity = match_components(X, Y)
        self.assertGreaterEqual(similarity.sum() + 1e-12, np.trace(cosine_matrix(X, Y)))

    def test_zero_columns_have_zero_similarity(self) -> None:
        X = np.array([[1.0, 0.0], [0.0, 0.0]])
        assert_array_equal(cosine_matrix(X, X), [[1, 0], [0, 0]])

    def test_compare_to_first_reports_matched_and_same_index_similarity(self) -> None:
        W = np.eye(3) + 0.1
        runs = [{"seed": 0, "W": W}, {"seed": 1, "W": W[:, [2, 0, 1]] * 3}]
        (row,) = compare_to_first(runs)
        self.assertAlmostEqual(row["matched_mean"], 1)
        self.assertEqual(row["matched_above_0.99"], 3)
        self.assertLess(row["same_index_mean"], 0.5)

    def test_pairwise_covers_every_pair_and_flags_an_unusual_seed(self) -> None:
        W = np.eye(4) + 0.1
        other = np.random.default_rng(6).random((4, 4))
        runs = [{"seed": 0, "W": other}, {"seed": 1, "W": W}, {"seed": 2, "W": W[:, [3, 1, 0, 2]] * 2}]
        summary = pairwise(runs)
        self.assertEqual(summary["pairs"], 3)
        self.assertAlmostEqual(summary["matched_mean"]["max"], 1)
        # Seeds 1 and 2 agree; the first seed is the odd one out and has the lowest mean.
        per_seed = summary["per_seed_mean"]
        self.assertLess(per_seed["0"], min(per_seed["1"], per_seed["2"]))


class FactorTests(unittest.TestCase):
    def test_run_starts_records_each_seed(self) -> None:
        rng = np.random.default_rng(5)
        A = rng.uniform(0.5, 1.5, (6, 2)) @ rng.uniform(0.5, 1.5, (2, 7))
        runs = run_starts(A, 2, [0, 1], "kl", max_iter=200, tol=0)
        self.assertEqual([run["seed"] for run in runs], [0, 1])
        for run in runs:
            self.assertLessEqual(run["final"], run["initial"])
            self.assertEqual(run["W"].shape, (6, 2))
            self.assertEqual(len(run["stationarity_start"]), 2)
            assert_allclose(run["stationarity_end_relative"],
                            np.array(run["stationarity_end"]) / np.linalg.norm(A))


if __name__ == "__main__":
    unittest.main()
