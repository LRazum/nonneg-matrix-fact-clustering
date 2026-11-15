"""GuitarSet recordings: listing tracks and, later, loading audio and notes.

``root`` is the folder into which the two GuitarSet 1.1.0 archives (Zenodo record 3371780)
are unpacked, normally ``data/raw``::

    root/annotation/<track_id>.jams
    root/audio_mono-mic/<track_id>_mic.wav

A track id looks like ``00_BN1-129-Eb_comp``: player (00-05), style and chord progression
(BN, Funk, Jazz, Rock or SS with 1-3), tempo in BPM, key, and mode (``comp`` or ``solo``).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ANNOTATION_DIR = "annotation"
AUDIO_DIR = "audio_mono-mic"
AUDIO_SUFFIX = "_mic.wav"
N_PLAYERS = 6
MODES = ("comp", "solo")
TRACKS_PER_PLAYER_AND_MODE = 30

"""Regular expression for file name parsing."""
_TRACK_ID = re.compile(
    r"(?P<player>0[0-5])_(?:BN|Funk|Jazz|Rock|SS)[1-3]-\d{2,3}-[A-G][#b]?_(?P<mode>comp|solo)"
)


@dataclass(frozen=True)
class Track:
    """One GuitarSet recording and the paths of its two files."""
    track_id: str
    player: int
    mode: str
    audio_path: Path
    annotation_path: Path


def parse_track_id(track_id: str) -> tuple[int, str]:
    """Return ``(player, mode)`` encoded in a GuitarSet track id."""
    match = _TRACK_ID.fullmatch(track_id)
    if match is None:
        raise ValueError(f"not a GuitarSet track id: {track_id!r}")
    return int(match["player"]), match["mode"]


def list_tracks(root: str | Path) -> list[Track]:
    """List all 360 GuitarSet tracks under ``root``, sorted by track id.

    Every annotation must have its audio file and vice versa, and each of the six players
    must have 30 ``comp`` and 30 ``solo`` tracks; otherwise an error is raised.
    """
    root = Path(root)
    annotation_dir = root / ANNOTATION_DIR
    audio_dir = root / AUDIO_DIR
    for directory in (annotation_dir, audio_dir):
        if not directory.is_dir():
            raise FileNotFoundError(f"missing GuitarSet folder: {directory}")

    annotation_ids = {path.stem for path in annotation_dir.glob("*.jams")}
    audio_ids = {
        path.name.removesuffix(AUDIO_SUFFIX) for path in audio_dir.glob(f"*{AUDIO_SUFFIX}")
    }
    if annotation_ids != audio_ids:
        no_audio = sorted(annotation_ids - audio_ids)
        no_annotation = sorted(audio_ids - annotation_ids)
        raise FileNotFoundError(
            f"unpaired GuitarSet files in {root}: annotations without audio {no_audio[:5]}, "
            f"audio without annotation {no_annotation[:5]}"
        )

    tracks = []
    for track_id in sorted(annotation_ids):
        player, mode = parse_track_id(track_id)
        tracks.append(
            Track(
                track_id=track_id,
                player=player,
                mode=mode,
                audio_path=audio_dir / f"{track_id}{AUDIO_SUFFIX}",
                annotation_path=annotation_dir / f"{track_id}.jams",
            )
        )
    _check_counts(tracks)
    return tracks


def _check_counts(tracks: list[Track]) -> None:
    counts = Counter((track.player, track.mode) for track in tracks)
    wrong = {
        (player, mode): counts[player, mode]
        for player in range(N_PLAYERS)
        for mode in MODES
        if counts[player, mode] != TRACKS_PER_PLAYER_AND_MODE
    }
    if wrong:
        raise ValueError(
            f"expected {TRACKS_PER_PLAYER_AND_MODE} tracks per (player, mode), got {wrong}"
        )