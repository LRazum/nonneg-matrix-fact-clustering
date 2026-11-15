import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from numpy.testing import assert_array_equal

from gitara.data import Track, list_tracks, load_notes, parse_track_id


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
            