import tempfile
import unittest
from pathlib import Path

from gitara.data import list_tracks, parse_track_id


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