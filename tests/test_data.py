import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal
from scipy.io import wavfile

from gitara.data import Track, list_tracks, load_audio, load_notes, parse_track_id


def make_fake_guitarset(root: Path) -> None:
    """Create empty files named like the full dataset: 6 players x 30 excerpts x 2 modes."""
    (root / "annotation").mkdir()
    (root / "audio_mono-mic").mkdir()
    for player in range(6):
        for excerpt in range(30):
            for mode in ("comp", "solo"):
                track_id = f"{player:02d}_Rock{excerpt % 3 + 1}-{100 + excerpt}-C#_{mode}"
                (root / "annotation" / f"{track_id}.jams").touch()
                (root / "audio_mono-mic" / f"{track_id}_mic.wav").touch()


class ParseTrackIdTests(unittest.TestCase):
    def test_reads_player_and_mode(self) -> None:
        self.assertEqual(parse_track_id("00_BN1-129-Eb_comp"), (0, "comp"))
        self.assertEqual(parse_track_id("05_Jazz2-187-F#_solo"), (5, "solo"))
        self.assertEqual(parse_track_id("03_SS3-84-Bb_comp"), (3, "comp"))

    def test_rejects_other_names(self) -> None:
        for name in ["06_BN1-129-Eb_comp", "00_BN1-129-Eb", "00_Pop1-100-C_comp",
                     "00_BN1-129-Eb_comp_mic", "0_BN1-129-Eb_solo", ""]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                parse_track_id(name)


class ListTracksTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        make_fake_guitarset(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_lists_all_tracks_sorted_with_paths(self) -> None:
        tracks = list_tracks(self.root)
        self.assertEqual(len(tracks), 360)
        ids = [track.track_id for track in tracks]
        self.assertEqual(ids, sorted(ids))
        first = tracks[0]
        self.assertEqual((first.player, first.mode), (0, "comp"))
        self.assertEqual(first.annotation_path, self.root / "annotation" / f"{first.track_id}.jams")
        self.assertEqual(first.audio_path, self.root / "audio_mono-mic" / f"{first.track_id}_mic.wav")
        for player in range(6):
            self.assertEqual(sum(track.player == player for track in tracks), 60)

    def test_missing_audio_file_is_reported(self) -> None:
        (self.root / "audio_mono-mic" / "02_Rock1-100-C#_solo_mic.wav").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "02_Rock1-100-C#_solo"):
            list_tracks(self.root)

    def test_missing_track_breaks_the_counts(self) -> None:
        (self.root / "annotation" / "04_Rock2-101-C#_comp.jams").unlink()
        (self.root / "audio_mono-mic" / "04_Rock2-101-C#_comp_mic.wav").unlink()
        with self.assertRaisesRegex(ValueError, r"\(4, 'comp'\): 29"):
            list_tracks(self.root)

    def test_unexpected_file_name_is_rejected(self) -> None:
        (self.root / "annotation" / "notes.jams").touch()
        (self.root / "audio_mono-mic" / "notes_mic.wav").touch()
        with self.assertRaisesRegex(ValueError, "notes"):
            list_tracks(self.root)

    def test_missing_folder_is_reported(self) -> None:
        with self.assertRaises(FileNotFoundError):
            list_tracks(self.root / "nowhere")

def note(time: float, duration: float, value: float) -> dict:
    return {"time": time, "duration": duration, "value": value, "confidence": None}


def note_annotation(string: int, notes: list[dict]) -> dict:
    return {
        "namespace": "note_midi",
        "annotation_metadata": {"data_source": str(string)},
        "data": notes,
    }


def small_jam() -> dict:
    """Two strings with three notes in total; the other four strings are silent."""
    annotations = [note_annotation(string, []) for string in range(6)]
    annotations[0] = note_annotation(0, [note(1.0, 0.5, 40.2)])
    annotations[4] = note_annotation(4, [note(0.25, 1.0, 64.9), note(2.0, 0.25, 67.0)])
    # A pitch contour stores its data as a dict of lists; it must be ignored.
    annotations.append({
        "namespace": "pitch_contour",
        "annotation_metadata": {"data_source": "0"},
        "data": {"time": [1.0], "duration": [0.0], "value": [{"frequency": 82.4}]},
    })
    return {"annotations": annotations, "file_metadata": {"title": "00_Rock1-100-C_comp"}}


class LoadNotesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "00_Rock1-100-C_comp.jams"
        self.track = Track("00_Rock1-100-C_comp", 0, "comp", Path("unused.wav"), self.path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, jam: dict) -> None:
        self.path.write_text(json.dumps(jam), encoding="utf-8")

    def test_reads_notes_sorted_by_onset(self) -> None:
        self.write(small_jam())
        intervals, pitches, strings = load_notes(self.track)
        assert_array_equal(intervals, [[0.25, 1.25], [1.0, 1.5], [2.0, 2.25]])
        assert_array_equal(pitches, [64.9, 40.2, 67.0])
        assert_array_equal(strings, [4, 0, 4])
        self.assertEqual(intervals.dtype, np.float64)
        self.assertEqual(strings.dtype, np.int64)

    def test_silent_track_gives_empty_arrays_of_the_right_shape(self) -> None:
        self.write({"annotations": [note_annotation(string, []) for string in range(6)]})
        intervals, pitches, strings = load_notes(self.track)
        self.assertEqual((intervals.shape, pitches.shape, strings.shape), ((0, 2), (0,), (0,)))

    def test_bad_notes_are_rejected_with_the_track_id(self) -> None:
        for bad in (note(1.0, 0.0, 50.0), note(1.0, -0.1, 50.0), note(-1.0, 0.5, 50.0),
                    note(1.0, 0.5, float("nan"))):
            jam = small_jam()
            jam["annotations"][2] = note_annotation(2, [bad])
            self.write(jam)
            with self.subTest(note=bad), self.assertRaisesRegex(ValueError, "00_Rock1-100-C_comp"):
                load_notes(self.track)

    def test_each_string_must_appear_exactly_once(self) -> None:
        jam = small_jam()
        del jam["annotations"][5]
        self.write(jam)
        with self.assertRaisesRegex(ValueError, "each string"):
            load_notes(self.track)
        jam = small_jam()
        jam["annotations"][5]["annotation_metadata"]["data_source"] = "4"
        self.write(jam)
        with self.assertRaisesRegex(ValueError, "each string"):
            load_notes(self.track)

    def test_unknown_string_label_is_rejected(self) -> None:
        jam = small_jam()
        jam["annotations"][5]["annotation_metadata"]["data_source"] = "6"
        self.write(jam)
        with self.assertRaisesRegex(ValueError, "string label"):
            load_notes(self.track)

    def test_malformed_file_is_rejected(self) -> None:
        jam = small_jam()
        del jam["annotations"][0]["data"][0]["duration"]
        self.write(jam)
        with self.assertRaisesRegex(ValueError, "malformed"):
            load_notes(self.track)

    def test_missing_file_is_reported(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_notes(self.track)


def sine(frequency: float, seconds: float = 1.0, rate: int = 44_100, amplitude: float = 0.5):
    """A 16-bit PCM sine wave, as stored in a GuitarSet WAV file."""
    time = np.arange(int(seconds * rate)) / rate
    return np.round(amplitude * 32_767 * np.sin(2 * np.pi * frequency * time)).astype(np.int16)


class LoadAudioTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "00_Rock1-100-C_comp_mic.wav"
        self.track = Track("00_Rock1-100-C_comp", 0, "comp", self.path, Path("unused.jams"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, samples: np.ndarray, rate: int = 44_100) -> None:
        wavfile.write(self.path, rate, samples)

    def test_original_rate_only_rescales_samples(self) -> None:
        self.write(np.array([-32_768, 0, 16_384, 32_767], dtype=np.int16))
        signal = load_audio(self.track, sr=44_100)
        assert_array_equal(signal, [-1.0, 0.0, 0.5, 32_767 / 32_768])
        self.assertEqual(signal.dtype, np.float64)

    def test_resampled_sine_keeps_its_frequency_and_amplitude(self) -> None:
        self.write(sine(440.0))
        signal = load_audio(self.track)
        self.assertEqual(signal.shape, (22_050,))
        spectrum = np.abs(np.fft.rfft(signal))
        frequencies = np.fft.rfftfreq(signal.size, d=1 / 22_050)
        self.assertEqual(frequencies[np.argmax(spectrum)], 440.0)
        middle = signal[2_000:-2_000]  # away from the filter's edge effects
        assert_allclose(np.sqrt(np.mean(middle**2)), 0.5 / np.sqrt(2), rtol=1e-3)

    def test_content_above_the_new_nyquist_frequency_is_removed(self) -> None:
        self.write(sine(15_000.0))  # above 22 050 / 2 = 11 025 Hz
        signal = load_audio(self.track)[2_000:-2_000]
        self.assertLess(np.sqrt(np.mean(signal**2)), 1e-3 * 0.5 / np.sqrt(2))

    def test_unexpected_formats_are_rejected(self) -> None:
        cases = {
            "stereo": (np.zeros((100, 2), dtype=np.int16), 44_100),
            "48 kHz": (np.zeros(100, dtype=np.int16), 48_000),
            "float samples": (np.zeros(100, dtype=np.float32), 44_100),
        }
        for label, (samples, rate) in cases.items():
            self.write(samples, rate)
            with self.subTest(label), self.assertRaisesRegex(ValueError, "00_Rock1-100-C_comp"):
                load_audio(self.track)

    def test_invalid_sample_rate_is_rejected(self) -> None:
        self.write(sine(440.0, seconds=0.01))
        for sr in (0, -22_050, 22_050.0, True):
            with self.subTest(sr=sr), self.assertRaises(ValueError):
                load_audio(self.track, sr=sr)

    def test_missing_file_is_reported(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_audio(self.track)