"""Pattern-based file renaming."""

import re
import sys
from pathlib import Path
from typing import List, Optional, Union

from . import file_utils
from ..core.track import Track

# Characters illegal in filenames: Windows-superset covers macOS/Linux too.
_ILLEGAL_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_TRAILING_DOTS_SPACES_RE = re.compile(r'[\s.]+$')


def sanitize_filename(name: str) -> str:
    """Remove or replace characters that are illegal in filenames.

    Applies the strictest rules (Windows superset) so the result is safe on
    all platforms.  Colons are replaced with a dash; all other illegal chars
    are stripped.  Reserved Windows names (CON, NUL, …) are prefixed with '_'.
    """
    # Replace colon with dash (common in titles like "Artist: Album")
    name = name.replace(":", " -")
    # Strip all other illegal characters
    name = _ILLEGAL_CHARS_RE.sub("", name)
    # Remove trailing dots and spaces (illegal on Windows)
    name = _TRAILING_DOTS_SPACES_RE.sub("", name)

    # Guard against reserved Windows device names (CON, PRN, AUX, NUL, COM1…9, LPT1…9)
    _RESERVED = {
        "CON", "PRN", "AUX", "NUL",
        *[f"COM{i}" for i in range(1, 10)],
        *[f"LPT{i}" for i in range(1, 10)],
    }
    stem = Path(name).stem.upper()
    if stem in _RESERVED:
        name = "_" + name

    return name or "_"


def generate_filename(track: Track, pattern: str) -> str:
    """Generate a new filename based on pattern placeholders."""
    replacements = {
        "%artist%":   track.artist,
        "%album%":    track.album,
        "%title%":    track.title,
        "%track%":    str(track.track_number),
        "%track2%":   str(track.track_number).zfill(2),
        "%track3%":   str(track.track_number).zfill(3),
        "%disc%":     str(track.disc_number),
        "%genre%":    track.genre,
        "%year%":     str(track.year),
        "%comment%":  track.comment,
        "%composer%": track.composer,
        "%grouping%": track.grouping,
        "%bpm%":      str(track.bpm),
        "%filename%": Path(track.file_path).stem,
        "%ext%":      Path(track.file_path).suffix[1:],  # without dot
    }

    result = pattern
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    # Sanitize each path component separately so sub-directories survive
    parts = Path(result).parts
    sanitized = Path(*[sanitize_filename(p) for p in parts]) if parts else Path("_")
    return str(sanitized)


def rename_track(
    track: Track,
    pattern: str,
    base_dir: Optional[Union[str, Path]] = None,
) -> bool:
    """Rename track file according to pattern."""
    new_name = generate_filename(track, pattern)

    base_dir = Path(base_dir) if base_dir is not None else Path(track.file_path).parent
    dest_path = base_dir / new_name

    # Ensure destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Nothing to do if source == destination
    if dest_path == track.file_path:
        return True

    if file_utils.safe_move(str(track.file_path), str(dest_path)):
        # FIX: use public update_path() instead of touching _file_path directly
        track.update_path(dest_path)
        return True
    return False


def rename_tracks(
    tracks: List[Track],
    pattern: str,
    base_dir: Optional[Union[str, Path]] = None,
) -> dict[int, bool]:
    """Rename multiple tracks; returns {index: success} mapping."""
    return {i: rename_track(track, pattern, base_dir) for i, track in enumerate(tracks)}
