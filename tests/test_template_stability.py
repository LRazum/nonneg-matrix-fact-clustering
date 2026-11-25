import unittest
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from experiments.template_stability import fold_tracks, learn_masked, pairwise_similarity
from gitara.data import Track


class SimilarityTests(unittest.TestCase):
    def test_scaled_templates_are_identical_and_orthogonal_ones_are_not(self) -> None:
        W = np.array([[1.0, 0.0], [2.0, 1.0], [0.0, 3.0]])
        mean, smallest = pairwise_similarity([W, 2 * W, 0.5 * W])
        assert_allclose(mean, 1)
        assert_allclose(smallest, 1)
        mean, _ = pairwise_similarity([np.eye(2), np.eye(2)[:, ::-1]])
        assert_array_equal(mean, [0, 0])

    def test_zero_column_has_no_value_and_min_is_at_most_mean(self) -> None:
        rng = np.random.default_rng(6)
        Ws = [rng.random((5, 3)) for _ in range(4)]
        Ws[2][:, 1] = 0
        mean, smallest = pairwise_similarity(Ws)
        self.assertTrue(np.isnan(mean[1]) and np.isnan(smallest[1]))
        self.assertTrue(np.all(smallest[[0, 2]] <= mean[[0, 2]]))


class LearningTests(unittest.TestCase):
    def test_stand_in_learner_keeps_unlabelled_pitches_inactive(self) -> None:
        rng = np.random.default_rng(7)
        rolls = [np.array([[1, 1, 0], [0, 0, 0], [0, 1, 1]], dtype=bool)]
        blocks = [rng.random((6, 3))]
        W, n_iter = learn_masked(blocks, rolls, objective="kl", seed=0, max_iter=50, tol=0)
        self.assertEqual((W.shape, n_iter), ((6, 4), 50))
        assert_array_equal(W[:, 1], 0)
        self.assertTrue(np.all(W[:, [0, 2, 3]].sum(axis=0) > 0))

    def test_fold_leaves_out_its_test_player(self) -> None:
        sample = [Track(f"0{p}_x_comp", p, "comp", Path("a"), Path("b")) for p in range(6)]
        self.assertEqual([t.player for t in fold_tracks(sample, 2)], [0, 1, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()
