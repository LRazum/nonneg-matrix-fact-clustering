import unittest
import warnings

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal
from scipy.signal import stft

from gitara.spectrogram import (
    PITCHES,
    hann,
    hz_to_midi,
    midi_to_hz,
    piano_roll,
    stft_magnitude,
)

SR = 22_050


def sine(frequency: float, seconds: float = 1.0, amplitude: float = 1.0, phase: float = 0.3):
    time = np.arange(int(seconds * SR)) / SR
    return amplitude * np.sin(2 * np.pi * frequency * time + phase)


class StftTests(unittest.TestCase):
    def test_sine_at_a_bin_frequency(self) -> None:
        n_win, bin_index, amplitude = 2048, 100, 0.5
        frequency = bin_index * SR / n_win  # about 1076.66 Hz, exactly on bin 100
        A, freqs, _ = stft_magnitude(sine(frequency, amplitude=amplitude), n_win=n_win)
        self.assertEqual(freqs[bin_index], frequency)
        interior = A[:, 4:-4]  # frames that lie completely inside the signal
        assert_array_equal(np.argmax(interior, axis=0), bin_index)
        # A sine is two complex exponentials of amplitude a / 2; the window sum scales each one.
        expected = amplitude * hann(n_win).sum() / 2
        assert_allclose(interior[bin_index], expected, rtol=1e-9)

    def test_matches_scipy_stft(self) -> None:
        rng = np.random.default_rng(0)
        y = rng.standard_normal(10_000)
        A, freqs, times = stft_magnitude(y, f_max=SR / 2)
        f, t, Z = stft(y, fs=SR, window="hann", nperseg=2048, noverlap=2048 - 512,
                       boundary="zeros", padded=True, detrend=False)
        n = A.shape[1]
        # scipy divides by the window sum; it may append frames past the end of the signal.
        assert_allclose(A, np.abs(Z[:, :n]) * hann(2048).sum(), rtol=1e-9, atol=1e-9)
        assert_allclose(freqs, f)
        assert_allclose(times, t[:n])

    def test_magnitudes_of_distant_sines_add_up(self) -> None:
        low, high = sine(220.0, amplitude=0.6), sine(1_500.0, amplitude=0.3, phase=1.1)
        both = stft_magnitude(low + high)[0]
        separate = stft_magnitude(low)[0] + stft_magnitude(high)[0]
        # |X1 + X2| <= |X1| + |X2| always holds (triangle inequality) ...
        self.assertTrue(np.all(both <= separate + 1e-9))
        # ... and with little spectral overlap it is almost an equality. The first and last
        # frames are left out: the abrupt start and end of the sines spread energy over all bins.
        interior = slice(4, -4)
        error = np.linalg.norm(both[:, interior] - separate[:, interior])
        self.assertLess(error / np.linalg.norm(separate[:, interior]), 1e-4)

    def test_frame_times_and_shape(self) -> None:
        A, freqs, times = stft_magnitude(np.zeros(1_000), hop=512)
        assert_allclose(times, [0.0, 512 / SR])  # centres on samples 0 and 512 of 0..999
        self.assertEqual(A.shape, (freqs.size, 2))
        self.assertTrue(freqs[-1] <= 5_500.0 < freqs[-1] + SR / 2048)
        self.assertEqual(freqs.size, 511)  # bins 0..510 lie at or below 5.5 kHz

    def test_output_is_nonnegative_and_finite(self) -> None:
        y = np.random.default_rng(1).standard_normal(5_000)
        A, _, _ = stft_magnitude(y)
        self.assertEqual(A.dtype, np.float64)
        self.assertTrue(np.all(A >= 0) and np.all(np.isfinite(A)))

    def test_invalid_input_is_rejected(self) -> None:
        y = np.zeros(1_000)
        bad_signals = {"nan": np.array([0.0, np.nan]), "empty": np.zeros(0),
                       "stereo": np.zeros((10, 2))}
        for label, signal in bad_signals.items():
            with self.subTest(label), self.assertRaises(ValueError):
                stft_magnitude(signal)
        bad_options = [{"hop": 0}, {"hop": 4_096}, {"n_win": 2_047}, {"n_win": 2_048.0},
                       {"f_max": 0}, {"f_max": SR}, {"sr": True}]
        for options in bad_options:
            with self.subTest(**options), self.assertRaises(ValueError):
                stft_magnitude(y, **options)


class PitchTests(unittest.TestCase):
    def test_reference_pitches(self) -> None:
        assert_allclose(midi_to_hz([69, 57, 81, 40]), [440.0, 220.0, 880.0, 82.4068892282175])
        assert_allclose(hz_to_midi([440.0, 220.0, 82.4068892282175]), [69, 57, 40])

    def test_conversions_are_inverse(self) -> None:
        pitches = np.linspace(30, 100, 71)
        assert_allclose(hz_to_midi(midi_to_hz(pitches)), pitches)

    def test_invalid_frequency_is_rejected(self) -> None:
        for frequency in (0.0, -1.0, np.nan):
            with self.subTest(frequency=frequency), self.assertRaises(ValueError):
                hz_to_midi(frequency)

    def test_pitch_range(self) -> None:
        self.assertEqual((PITCHES[0], PITCHES[-1], PITCHES.size), (40, 88, 49))


class PianoRollTests(unittest.TestCase):
    times = np.arange(6) * 0.5  # frame times 0.0, 0.5, ..., 2.5 s

    def test_hand_made_notes(self) -> None:
        intervals = np.array([[0.0, 1.0], [0.4, 0.6], [1.2, 2.6], [1.0, 1.4]])
        pitches = np.array([40.2, 41.5, 40.0, 42.4])  # rounded: 40, 42, 40, 42
        roll = piano_roll(intervals, pitches, self.times, pitch_set=np.array([40, 41, 42]))
        expected = np.array([
            [1, 1, 0, 1, 1, 1],  # [0.0, 1.0) covers 0.0 and 0.5; [1.2, 2.6) covers 1.5..2.5
            [0, 0, 0, 0, 0, 0],
            [0, 1, 1, 0, 0, 0],  # [0.4, 0.6) covers 0.5; [1.0, 1.4) covers 1.0
        ], dtype=bool)
        assert_array_equal(roll, expected)
        self.assertEqual(roll.dtype, np.bool_)

    def test_notes_outside_the_range_are_counted_and_reported(self) -> None:
        intervals = np.array([[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]])
        with self.assertWarnsRegex(UserWarning, "2 of 3 notes"):
            roll = piano_roll(intervals, np.array([39.4, 40.0, 89.0]), self.times)
        self.assertEqual(roll.shape, (49, 6))
        assert_array_equal(np.flatnonzero(roll.any(axis=1)), [0])

    def test_no_notes_gives_an_empty_roll_without_warning(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            roll = piano_roll(np.zeros((0, 2)), np.zeros(0), self.times)
        self.assertFalse(roll.any())

    def test_invalid_notes_are_rejected(self) -> None:
        cases = {
            "end before start": (np.array([[1.0, 0.5]]), np.array([40.0]), self.times),
            "nan pitch": (np.array([[0.0, 1.0]]), np.array([np.nan]), self.times),
            "shape mismatch": (np.array([[0.0, 1.0]]), np.array([40.0, 41.0]), self.times),
            "unsorted times": (np.array([[0.0, 1.0]]), np.array([40.0]), self.times[::-1]),
        }
        for label, args in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                piano_roll(*args)
