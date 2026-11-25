import unittest

import numpy as np

from gitara import nmf, transcribe

PITCHES = np.array([40.0, 41.0, 42.0])
STEP = 0.1


def times(n: int) -> np.ndarray:
    return np.arange(n) * STEP


def notes(H, n=None, **kwargs):
    H = np.asarray(H, dtype=float)
    params = dict(frame_step=STEP, threshold=0.5, min_duration=0.0)
    params.update(kwargs)
    return transcribe.extract_notes(H, times(H.shape[1]), PITCHES, **params)


def block(rows: dict[int, list[float]], n: int) -> np.ndarray:
    H = np.zeros((3, n))
    for k, values in rows.items():
        H[k, :len(values)] = values
    return H


class ExtractNotesTests(unittest.TestCase):
    def test_known_blocks_give_exact_notes(self) -> None:
        H = np.zeros((3, 10))
        H[0, 2:5] = 1.0
        H[2, 6:8] = 0.8
        intervals, pitches = notes(H)
        np.testing.assert_allclose(intervals, [[0.2, 0.5], [0.6, 0.8]])
        np.testing.assert_array_equal(pitches, [40.0, 42.0])

    def test_run_reaching_last_frame_ends_one_step_later(self) -> None:
        H = np.zeros((3, 10))
        H[1, 7:] = 1.0
        intervals, pitches = notes(H)
        np.testing.assert_allclose(intervals, [[0.7, 1.0]])
        np.testing.assert_array_equal(pitches, [41.0])

    def test_threshold_is_inclusive_after_normalization(self) -> None:
        H = block({0: [1.0, 0.5, 0.49, 0.0]}, 4)
        intervals, _ = notes(H, threshold=0.5)
        np.testing.assert_allclose(intervals, [[0.0, 0.2]])

    def test_short_note_is_dropped(self) -> None:
        H = block({0: [0, 1, 0, 0, 1, 1, 1, 0]}, 8)
        intervals, _ = notes(H, min_duration=0.15)
        np.testing.assert_allclose(intervals, [[0.4, 0.7]])
        intervals, _ = notes(H, min_duration=0.1)
        self.assertEqual(len(intervals), 2)

    def test_repeated_attack_is_split_only_with_retrigger(self) -> None:
        H = block({0: [1.0, 0.6, 0.6, 1.0, 0.9, 0.0]}, 6)
        intervals, _ = notes(H)
        np.testing.assert_allclose(intervals, [[0.0, 0.5]])
        intervals, pitches = notes(H, retrigger=0.3)
        np.testing.assert_allclose(intervals, [[0.0, 0.3], [0.3, 0.5]])
        np.testing.assert_array_equal(pitches, [40.0, 40.0])

    def test_attack_smeared_over_several_frames_is_one_note(self) -> None:
        # The window smears an onset over 3-4 frames: every rise exceeds delta, but only one
        # of them is the steepest, and the run starts above the threshold, so no split at all.
        H = block({0: [0.1, 0.4, 0.8, 1.0, 1.0, 0.0]}, 6)
        intervals, _ = notes(H, retrigger=0.1)
        np.testing.assert_allclose(intervals, [[0.2, 0.5]])
        # Even when the whole ramp is inside the run (first frame already above a small
        # threshold) it is one attack, because the activation never fell before the steep frame.
        intervals, _ = notes(H, retrigger=0.1, threshold=0.05)
        np.testing.assert_allclose(intervals, [[0.0, 0.5]])
        H = block({0: [0.1, 0.4, 0.8, 1.0, 1.0, 0.0]}, 6)
        intervals, _ = notes(H, retrigger=0.2, threshold=0.05)
        np.testing.assert_allclose(intervals, [[0.0, 0.5]])

    def test_attack_after_a_fall_inside_the_run_splits_once_and_needs_a_new_fall(self) -> None:
        # Fall at frame 1, steepest rise at frame 3 -> split there. The following ramp
        # (frames 5-6) has no fall since that cut, so it does not split again.
        H = block({0: [1.0, 0.6, 0.6, 0.9, 0.95, 1.0, 1.0, 0.0]}, 8)
        intervals, _ = notes(H, retrigger=0.25, threshold=0.05)
        np.testing.assert_allclose(intervals, [[0.0, 0.3], [0.3, 0.7]])

    def test_second_attack_with_a_ramp_splits_once_at_its_steepest_frame(self) -> None:
        H = block({0: [1.0, 0.5, 0.5, 0.7, 1.0, 1.0, 0.0]}, 7)
        intervals, _ = notes(H, retrigger=0.2)
        np.testing.assert_allclose(intervals, [[0.0, 0.4], [0.4, 0.6]])

    def test_equal_rises_split_once_at_the_last_frame_of_the_plateau(self) -> None:
        H = block({0: [0.5, 0.5, 0.75, 1.0, 1.0, 0.0]}, 6)  # rises 0.25, 0.25 (exact in binary)
        intervals, _ = notes(H, retrigger=0.2)
        self.assertEqual(len(intervals), 2)
        np.testing.assert_allclose(intervals, [[0.0, 0.3], [0.3, 0.5]])

    def test_zero_matrix_and_zero_row(self) -> None:
        intervals, pitches = notes(np.zeros((3, 5)))
        self.assertEqual((intervals.shape, pitches.shape), ((0, 2), (0,)))
        intervals, pitches = notes(block({1: [0, 1, 1, 0]}, 4))
        self.assertEqual(pitches.tolist(), [41.0])

    def test_background_row_is_ignored_including_in_normalization(self) -> None:
        H = np.zeros((4, 5))
        H[0, 1:3] = 1.0
        H[3, :] = 100.0
        intervals, pitches = notes(H)
        np.testing.assert_allclose(intervals, [[0.1, 0.3]])
        np.testing.assert_array_equal(pitches, [40.0])

    def test_single_frame_input(self) -> None:
        intervals, pitches = notes(np.array([[0.0], [2.0], [0.0]]))
        np.testing.assert_allclose(intervals, [[0.0, 0.1]])
        np.testing.assert_array_equal(pitches, [41.0])

    def test_notes_are_sorted_by_onset_then_pitch(self) -> None:
        H = block({0: [0, 0, 1, 1], 1: [1, 1, 0, 0], 2: [0, 0, 1, 1]}, 4)
        intervals, pitches = notes(H)
        np.testing.assert_allclose(intervals[:, 0], [0.0, 0.2, 0.2])
        np.testing.assert_array_equal(pitches, [41.0, 40.0, 42.0])

    def test_invalid_input_raises_value_error(self) -> None:
        good = block({0: [1, 1]}, 2)
        bad_inputs = [
            dict(H=np.array([[np.nan, 1.0]] * 3)),
            dict(H=-good),
            dict(H=good[:2]),
            dict(H=good, times=np.arange(3) * STEP),
            dict(H=good, threshold=0.0),
            dict(H=good, threshold=1.5),
            dict(H=good, frame_step=0.0),
            dict(H=good, min_duration=-1.0),
            dict(H=good, retrigger=0.0),
            dict(H=good[0]),
        ]
        for kwargs in bad_inputs:
            with self.subTest(kwargs=list(kwargs)):
                call = dict(
                    times=times(good.shape[1]), pitches=PITCHES, frame_step=STEP,
                    threshold=0.5, min_duration=0.0,
                )
                H = kwargs.pop("H")
                call.update(kwargs)
                with self.assertRaises(ValueError):
                    transcribe.extract_notes(H, **call)


class ActivationsTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(0)
        self.W = np.abs(rng.normal(size=(12, 3))) + 0.1
        self.W[:, 2] = 0.0  # inactive pitch
        self.H_true = np.zeros((3, 20))
        self.H_true[0, 3:9] = 1.0
        self.H_true[1, 10:18] = 2.0
        self.A = self.W @ self.H_true

    def test_shape_inactive_rows_and_objective_decrease(self) -> None:
        H = transcribe.activations(self.A, self.W, "kl", max_iter=500, tol=1e-9)
        self.assertEqual(H.shape, (3, 20))
        self.assertTrue(np.isfinite(H).all() and (H >= 0).all())
        self.assertTrue((H[2] == 0).all())
        H0 = np.zeros_like(H)
        H0[:2] = 1.0
        initial = nmf.kl_divergence(self.A, self.W @ H0)
        final = nmf.kl_divergence(self.A, self.W @ H)
        # A = W H* exactly and the active columns of W are linearly independent, so H* is the
        # unique minimizer with objective 0. Multiplicative updates approach the zeros of A only
        # slowly, hence the criterion is a drop of the objective by a factor 1e-3, not equality.
        self.assertLess(final, 1e-3 * initial)
        # On frames where H* > 0, H is close to H* (loose: slow convergence, see above).
        positive = self.H_true > 0
        np.testing.assert_allclose(H[positive], self.H_true[positive], rtol=0.1)

    def test_invalid_input_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            transcribe.activations(self.A, np.zeros_like(self.W))
        with self.assertRaises(ValueError):
            transcribe.activations(-self.A, self.W)
        with self.assertRaises(ValueError):
            transcribe.activations(self.A[:5], self.W)


if __name__ == "__main__":
    unittest.main()
