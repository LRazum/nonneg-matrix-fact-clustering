import importlib.util
import unittest
import warnings
from itertools import permutations

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from gitara.evaluate import note_scores, pool_scores


def notes(*rows: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    """Notes from (onset, pitch) pairs; every note lasts 0.2 s, since offsets are not compared."""
    onsets = np.array([onset for onset, _ in rows], dtype=float)
    intervals = np.column_stack((onsets, onsets + 0.2)) if rows else np.zeros((0, 2))
    return intervals, np.array([pitch for _, pitch in rows], dtype=float)


def allowed_pairs(ref, est, onset_tol=0.05, pitch_tol_cents=50.0) -> np.ndarray:
    return (np.abs(ref[0][:, :1] - est[0][:, 0]) <= onset_tol + 1e-9) & (
        100 * np.abs(ref[1][:, None] - est[1]) <= pitch_tol_cents + 1e-9
    )


def brute_force_tp(allowed: np.ndarray) -> int:
    """Largest matching by trying every assignment; only for a handful of notes."""
    n_ref, n_est = allowed.shape
    if n_ref > n_est:
        return brute_force_tp(allowed.T)
    choices = permutations(range(n_est), n_ref)
    return max((sum(allowed[i, j] for i, j in enumerate(c)) for c in choices), default=0)


def greedy_tp(ref, est) -> int:
    """Each estimate, in onset order, takes the closest free reference it is allowed to match."""
    allowed, free, tp = allowed_pairs(ref, est), set(range(len(ref[1]))), 0
    for j in np.argsort(est[0][:, 0]):
        candidates = [i for i in free if allowed[i, j]]
        if candidates:
            free.remove(min(candidates, key=lambda i: abs(ref[0][i, 0] - est[0][j, 0])))
            tp += 1
    return tp


class NoteScoresTests(unittest.TestCase):
    def test_identical_lists_score_one(self) -> None:
        ref = notes((0.0, 40.0), (0.5, 52.3), (0.5, 56.0), (1.2, 64.0))
        scores = note_scores(*ref, *ref)
        self.assertEqual((scores.precision, scores.recall, scores.f1), (1.0, 1.0, 1.0))
        self.assertEqual(scores.tp, 4)
        assert_array_equal(scores.matches, [[0, 0], [1, 1], [2, 2], [3, 3]])

    def test_onset_tolerance_boundary(self) -> None:
        ref = notes((1.0, 60.0))
        for shift, hit in ((0.049, True), (0.050, True), (-0.050, True), (0.051, False)):
            with self.subTest(shift=shift):
                self.assertEqual(note_scores(*ref, *notes((1.0 + shift, 60.0))).tp, int(hit))

    def test_pitch_tolerance_and_octave_error(self) -> None:
        ref = notes((1.0, 60.0))
        cases = ((60.49, True), (60.5, True), (59.5, True), (60.51, False), (61.0, False),
                 (72.0, False), (48.0, False))  # 72 and 48 are octave errors
        for pitch, hit in cases:
            with self.subTest(pitch=pitch):
                self.assertEqual(note_scores(*ref, *notes((1.0, pitch))).tp, int(hit))

    def test_one_estimate_matches_at_most_one_reference(self) -> None:
        # Two reference notes (a unison on two strings) and one estimate that fits both.
        scores = note_scores(*notes((1.0, 50.0), (1.01, 50.0)), *notes((1.0, 50.0)))
        self.assertEqual((scores.tp, scores.n_ref, scores.n_est), (1, 2, 1))
        assert_allclose((scores.precision, scores.recall, scores.f1), (1.0, 0.5, 2 / 3))

    def test_maximum_matching_beats_greedy_matching(self) -> None:
        # Estimate X (0.03 s) is closest to reference B (0.04 s) but can also match A (0.00 s);
        # estimate Y (0.08 s) can only match B. Greedy pairs X-B and leaves Y unmatched.
        ref = notes((0.00, 60.0), (0.04, 60.0))
        est = notes((0.03, 60.0), (0.08, 60.0))
        self.assertEqual(greedy_tp(ref, est), 1)
        scores = note_scores(*ref, *est)
        self.assertEqual(scores.tp, 2)
        assert_array_equal(scores.matches, [[0, 0], [1, 1]])

    def test_matches_brute_force_on_small_random_cases(self) -> None:
        rng = np.random.default_rng(0)
        for case in range(200):
            ref = notes(*zip(rng.uniform(0, 0.3, rng.integers(0, 6)).round(2),
                             rng.choice([60.0, 60.3, 61.0], 6)))
            est = notes(*zip(rng.uniform(0, 0.3, rng.integers(0, 6)).round(2),
                             rng.choice([60.0, 60.3, 61.0], 6)))
            with self.subTest(case=case), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                scores = note_scores(*ref, *est)
                self.assertEqual(scores.tp, brute_force_tp(allowed_pairs(ref, est)))
                for i, j in scores.matches:  # every reported pair is allowed and used once
                    self.assertTrue(allowed_pairs(ref, est)[i, j])
                self.assertEqual(len(set(scores.matches[:, 1])), scores.tp)

    def test_empty_lists(self) -> None:
        ref = notes((0.0, 60.0), (1.0, 62.0))
        with self.assertWarnsRegex(UserWarning, "precision is undefined"):
            scores = note_scores(*ref, *notes())
        self.assertTrue(np.isnan(scores.precision))
        self.assertEqual((scores.recall, scores.f1, scores.tp), (0.0, 0.0, 0))
        with self.assertWarnsRegex(UserWarning, "recall is undefined"):
            scores = note_scores(*notes(), *ref)
        self.assertTrue(np.isnan(scores.recall))
        self.assertEqual((scores.precision, scores.f1), (0.0, 0.0))
        self.assertEqual(scores.matches.shape, (0, 2))

    def test_no_hits_gives_zero_without_warning(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            scores = note_scores(*notes((0.0, 60.0)), *notes((1.0, 60.0)))
        self.assertEqual((scores.precision, scores.recall, scores.f1), (0.0, 0.0, 0.0))

    def test_invalid_input_is_rejected(self) -> None:
        good = notes((0.0, 60.0))
        cases = {
            "nan pitch": (*good, np.array([[0.0, 0.2]]), np.array([np.nan])),
            "end before start": (*good, np.array([[0.2, 0.1]]), np.array([60.0])),
            "negative onset": (*good, np.array([[-0.01, 0.2]]), np.array([60.0])),
            "shape mismatch": (*good, np.array([[0.0, 0.2]]), np.array([60.0, 61.0])),
        }
        for label, args in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                note_scores(*args)
        with self.assertRaises(ValueError):
            note_scores(*good, *good, onset_tol=-0.01)


class PoolScoresTests(unittest.TestCase):
    def test_counts_are_summed_before_dividing(self) -> None:
        # Track 1: 2 of 2 reference notes found, no false notes, so F1 = 1.
        first = note_scores(*notes((0.0, 60.0), (1.0, 62.0)), *notes((0.0, 60.0), (1.0, 62.0)))
        # Track 2: 1 of 8 reference notes found with 1 estimate, so P = 1, R = 1/8, F1 = 2/9.
        reference = notes(*[(float(t), 60.0) for t in range(8)])
        second = note_scores(*reference, *notes((0.0, 60.0)))
        pooled = pool_scores([first, second])
        self.assertEqual((pooled.tp, pooled.n_ref, pooled.n_est, pooled.n_tracks), (3, 10, 3, 2))
        assert_allclose((pooled.precision, pooled.recall, pooled.f1), (1.0, 0.3, 6 / 13))
        # The pooled F1 is not the mean of the per-track F1 values, (1 + 2/9) / 2 = 11/18.
        self.assertNotAlmostEqual(pooled.f1, (first.f1 + second.f1) / 2)

    def test_one_track_pools_to_itself(self) -> None:
        single = note_scores(*notes((0.0, 60.0), (1.0, 62.0)), *notes((0.0, 60.0)))
        pooled = pool_scores([single])
        self.assertEqual((pooled.precision, pooled.recall, pooled.f1, pooled.tp),
                         (single.precision, single.recall, single.f1, single.tp))

    def test_track_without_estimates_does_not_make_the_pool_undefined(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            silent = note_scores(*notes((0.0, 60.0)), *notes())
        found = note_scores(*notes((0.0, 60.0)), *notes((0.0, 60.0)))
        pooled = pool_scores([silent, found])
        assert_allclose((pooled.precision, pooled.recall, pooled.f1), (1.0, 0.5, 2 / 3))

    def test_no_estimates_at_all_and_no_tracks(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            silent = note_scores(*notes((0.0, 60.0)), *notes())
        with self.assertWarnsRegex(UserWarning, "precision is undefined"):
            pooled = pool_scores([silent, silent])
        self.assertTrue(np.isnan(pooled.precision))
        self.assertEqual(pooled.f1, 0.0)
        with self.assertRaises(ValueError):
            pool_scores([])


@unittest.skipUnless(importlib.util.find_spec("mir_eval"), "mir_eval is not installed")
class MirEvalComparisonTests(unittest.TestCase):
    def test_agrees_with_mir_eval_on_random_transcriptions(self) -> None:
        from mir_eval.transcription import precision_recall_f1_overlap

        def midi_to_hz(pitch):
            return 440.0 * 2.0 ** ((pitch - 69) / 12)

        rng = np.random.default_rng(1)
        for case in range(100):
            n_ref, n_est = rng.integers(1, 30, size=2)
            ref_onsets = np.sort(rng.uniform(0, 5, n_ref))
            ref_pitches = rng.integers(40, 70, n_ref) + rng.normal(0, 0.2, n_ref)
            # Estimates: jittered copies of some references plus random extra notes.
            keep = rng.random(n_ref) < 0.7
            jittered = np.maximum(ref_onsets[keep] + rng.normal(0, 0.04, keep.sum()), 0.0)
            est_onsets = np.concatenate((jittered, rng.uniform(0, 5, n_est)))
            est_pitches = np.concatenate((ref_pitches[keep] + rng.normal(0, 0.4, keep.sum()),
                                          rng.integers(40, 70, n_est).astype(float)))
            durations = rng.uniform(0.05, 1, n_ref)
            ref_intervals = np.column_stack((ref_onsets, ref_onsets + durations))
            est_intervals = np.column_stack((est_onsets, est_onsets + 0.1))
            ours = note_scores(ref_intervals, ref_pitches, est_intervals, est_pitches)
            theirs = precision_recall_f1_overlap(
                ref_intervals, midi_to_hz(ref_pitches), est_intervals, midi_to_hz(est_pitches),
                onset_tolerance=0.05, pitch_tolerance=50.0, offset_ratio=None,
            )
            with self.subTest(case=case):
                assert_allclose((ours.precision, ours.recall, ours.f1), theirs[:3], atol=1e-12)
