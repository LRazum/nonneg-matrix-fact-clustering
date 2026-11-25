"""GuitarSet recordings: download, listing tracks, and loading audio and notes.

``root`` is the folder into which the two GuitarSet 1.1.0 archives (Zenodo record 3371780)
are unpacked, normally ``data/raw``::

    root/annotation/<track_id>.jams
    root/audio_mono-mic/<track_id>_mic.wav

A track id looks like ``00_BN1-129-Eb_comp``: player (00-05), style and chord progression
(BN, Funk, Jazz, Rock or SS with 1-3), tempo in BPM, key, and mode (``comp`` or ``solo``).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import urllib.request
import zipfile
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import gcd
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

ANNOTATION_DIR = "annotation"
AUDIO_DIR = "audio_mono-mic"
AUDIO_SUFFIX = "_mic.wav"
N_PLAYERS = 6
MODES = ("comp", "solo")
TRACKS_PER_PLAYER_AND_MODE = 30
N_STRINGS = 6
NOTE_NAMESPACE = "note_midi"
SOURCE_SAMPLE_RATE = 44_100
SAMPLE_RATE = 22_050
INT16_SCALE = 32_768

DEFAULT_ROOT = Path("data", "raw")
DEFAULT_MANIFEST = Path("data", "manifest.csv")
ZENODO_URL = "https://zenodo.org/records/3371780/files/{name}?download=1"


@dataclass(frozen=True)
class Archive:
    """A GuitarSet archive on Zenodo and the folder it is unpacked into."""

    size: int
    md5: str
    folder: str
    suffix: str


# Size and MD5 from https://zenodo.org/api/records/3371780 (GuitarSet 1.1.0), checked 2026-11-14.
ARCHIVES = {
    "annotation.zip": Archive(
        39_132_574, "b39b78e63d3446f2e54ddb7a54df9b10", ANNOTATION_DIR, ".jams"
    ),
    "audio_mono-mic.zip": Archive(
        656_927_981, "275966d6610ac34999b58426beb119c3", AUDIO_DIR, AUDIO_SUFFIX
    ),
}

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


def load_notes(track: Track) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the annotated notes of ``track`` as ``(intervals, pitches, strings)``.

    ``intervals`` has shape ``(N, 2)`` with onset and offset in seconds, ``pitches`` has shape
    ``(N,)`` with the original non-integer MIDI pitch, and ``strings`` has shape ``(N,)`` with
    the string index 0-5. Notes are sorted by onset, then by string.

    A GuitarSet JAMS file is plain JSON. It has one ``note_midi`` annotation per string, and
    the string is given by ``annotation_metadata.data_source`` as the text ``"0"`` (low E)
    to ``"5"`` (high E). This was checked on ``00_BN1-129-Eb_comp``, where the pitch ranges
    rise with the index. Other annotations (pitch contours, chords, beats) are ignored.
    """
    path = track.annotation_path
    if not path.is_file():
        raise FileNotFoundError(f"missing annotation for {track.track_id}: {path}")
    with path.open(encoding="utf-8") as file:
        jam = json.load(file)

    rows: list[tuple[float, float, float, int]] = []
    seen_strings: list[int] = []
    try:
        for annotation in jam["annotations"]:
            if annotation["namespace"] != NOTE_NAMESPACE:
                continue
            string = _string_index(annotation["annotation_metadata"]["data_source"], track)
            seen_strings.append(string)
            for note in annotation["data"]:
                rows.append((note["time"], note["duration"], note["value"], string))
    except (KeyError, TypeError) as error:
        raise ValueError(f"malformed JAMS for {track.track_id}: {error!r}") from error

    if sorted(seen_strings) != list(range(N_STRINGS)):
        raise ValueError(
            f"{track.track_id}: expected one {NOTE_NAMESPACE} annotation for each string "
            f"0-{N_STRINGS - 1}, got strings {sorted(seen_strings)}"
        )

    table = np.array(rows, dtype=np.float64).reshape(-1, 4)
    onsets, durations, pitches, strings = table.T
    if not np.all(np.isfinite(table)):
        raise ValueError(f"{track.track_id}: non-finite note time, duration or pitch")
    if np.any(onsets < 0):
        raise ValueError(f"{track.track_id}: note with a negative onset")
    if np.any(durations <= 0):
        raise ValueError(f"{track.track_id}: note with a non-positive duration")

    order = np.lexsort((strings, onsets))
    intervals = np.column_stack((onsets, onsets + durations))[order]
    return intervals, pitches[order], strings[order].astype(np.int64)


def _string_index(data_source: object, track: Track) -> int:
    if not isinstance(data_source, str) or data_source not in {str(k) for k in range(N_STRINGS)}:
        raise ValueError(f"{track.track_id}: unexpected string label {data_source!r}")
    return int(data_source)


def load_audio(track: Track, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Return the microphone recording of ``track`` as ``float64`` samples at ``sr`` Hz.

    GuitarSet stores mono 16-bit PCM at 44 100 Hz. Samples are divided by 32 768, so the
    stored values lie in [-1, 1). For ``sr`` below 44 100 Hz the signal is resampled with
    ``scipy.signal.resample_poly``, whose low-pass filter removes content above the new
    Nyquist frequency ``sr / 2`` before decimation. After filtering, a few samples may lie
    slightly outside [-1, 1]; they are not clipped. The level is not normalized: whether and
    how to normalize is a separate, explicit preprocessing decision (task A4).
    """
    if isinstance(sr, bool) or not isinstance(sr, int) or sr <= 0:
        raise ValueError(f"sr must be a positive integer, got {sr!r}")
    path = track.audio_path
    if not path.is_file():
        raise FileNotFoundError(f"missing audio for {track.track_id}: {path}")

    rate, samples = wavfile.read(path)  # čita zaglavlje i vraća frekvenciju i polje uzoraka
    if samples.ndim != 1:
        raise ValueError(f"{track.track_id}: expected mono audio, got shape {samples.shape}")
    if samples.dtype != np.int16:
        raise ValueError(f"{track.track_id}: expected 16-bit PCM, got {samples.dtype}")
    if rate != SOURCE_SAMPLE_RATE:
        raise ValueError(f"{track.track_id}: expected {SOURCE_SAMPLE_RATE} Hz, got {rate} Hz")

    signal = samples.astype(np.float64) / INT16_SCALE  # pretvorba u float i u [-1, 1)
    if sr != rate:
        common = gcd(sr, rate)  # kraćenje omjera frekvencija
        signal = resample_poly(signal, sr // common, rate // common)  # filtar protiv aliasinga
    if not np.all(np.isfinite(signal)):
        raise ValueError(f"{track.track_id}: non-finite audio samples")
    return signal


def md5_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    """Return the MD5 checksum of a file, read in chunks of ``chunk_size`` bytes."""
    digest = hashlib.md5()
    with Path(path).open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _fetch(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url) as response, destination.open("wb") as file:
        shutil.copyfileobj(response, file)


def download(
    root: str | Path = DEFAULT_ROOT,
    archives: Mapping[str, Archive] = ARCHIVES,
    fetch: Callable[[str, Path], None] = _fetch,
) -> None:
    """Download the GuitarSet archives into ``root``, check them and unpack them.

    An archive that is already present with the right size and MD5 is not downloaded again.
    A download with the wrong size or MD5 is deleted and raises ``ValueError`` before anything
    is unpacked. Zenodo does not resume interrupted downloads, so a file is always fetched whole.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for name, archive in archives.items():
        path = root / name
        if not _archive_is_valid(path, archive):
            partial = path.with_name(path.name + ".part")
            fetch(ZENODO_URL.format(name=name), partial)
            if not _archive_is_valid(partial, archive):
                partial.unlink()
                raise ValueError(f"downloaded {name} does not match the expected size and MD5")
            partial.replace(path)
        _unpack(path, root / archive.folder, archive.suffix)


def _archive_is_valid(path: Path, archive: Archive) -> bool:
    if not path.is_file() or path.stat().st_size != archive.size:
        return False
    return md5_file(path) == archive.md5


def _unpack(path: Path, folder: Path, suffix: str) -> None:
    """Unpack a flat archive whose members are all named ``<track_id><suffix>``.

    Checking every name first also rules out paths that would escape ``folder``.
    """
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        for member in members:
            name = member.filename
            if not (name.endswith(suffix) and _TRACK_ID.fullmatch(name.removesuffix(suffix))):
                raise ValueError(f"unexpected member {name!r} in {path.name}")
        folder.mkdir(parents=True, exist_ok=True)
        for member in members:
            target_path = folder / member.filename
            with archive.open(member) as source, target_path.open("wb") as target:
                shutil.copyfileobj(source, target)


def _dataset_files(root: Path) -> list[Path]:
    files = []
    for track in list_tracks(root):
        files += [track.annotation_path, track.audio_path]
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def write_manifest(
    root: str | Path = DEFAULT_ROOT, manifest: str | Path = DEFAULT_MANIFEST
) -> None:
    """Write the size and MD5 of every annotation and audio file under ``root`` to a CSV file.

    Paths are relative to ``root`` and use ``/``, so the manifest is the same on every system.
    """
    root = Path(root)
    with Path(manifest).open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["path", "bytes", "md5"])
        for path in _dataset_files(root):
            name = path.relative_to(root).as_posix()
            writer.writerow([name, path.stat().st_size, md5_file(path)])


def verify_manifest(
    root: str | Path = DEFAULT_ROOT, manifest: str | Path = DEFAULT_MANIFEST
) -> None:
    """Check that the files under ``root`` are exactly those listed in ``manifest``.

    Raises ``ValueError`` naming missing, unexpected or changed files.
    """
    root = Path(root)
    with Path(manifest).open(newline="", encoding="utf-8") as file:
        expected = {row["path"]: (int(row["bytes"]), row["md5"]) for row in csv.DictReader(file)}
    actual = {path.relative_to(root).as_posix(): path for path in _dataset_files(root)}
    problems = [f"missing {name}" for name in sorted(expected.keys() - actual.keys())]
    problems += [f"unexpected {name}" for name in sorted(actual.keys() - expected.keys())]
    for name in sorted(expected.keys() & actual.keys()):
        path = actual[name]
        if (path.stat().st_size, md5_file(path)) != expected[name]:
            problems.append(f"changed {name}")
    if problems:
        raise ValueError(f"{len(problems)} file(s) differ from {manifest}: {problems[:5]}")


def main(argv: list[str] | None = None) -> None:
    """Command line: ``python -m gitara.data download`` or ``python -m gitara.data manifest``."""
    parser = argparse.ArgumentParser(
        prog="python -m gitara.data", description=__doc__.splitlines()[0]
    )
    parser.add_argument("command", choices=["download", "manifest"])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    if args.command == "download":
        download(args.root)
        tracks = list_tracks(args.root)
        if args.manifest.is_file():
            verify_manifest(args.root, args.manifest)
            print(f"{len(tracks)} tracks downloaded; all files match {args.manifest}")
        else:
            print(f"{len(tracks)} tracks downloaded; no manifest {args.manifest} to check against")
    else:
        write_manifest(args.root, args.manifest)
        print(f"manifest written to {args.manifest}")


if __name__ == "__main__":
    main()
