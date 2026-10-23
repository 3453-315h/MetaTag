"""iTunes library import/export."""

import logging
import os
import plistlib
import shutil
from pathlib import Path
from typing import List
from urllib.parse import quote, unquote, urlparse

from ..core.track import Track

logger = logging.getLogger(__name__)


def itunes_url_to_path(url: str) -> Path:
    """Convert iTunes file:// URL to local Path."""
    parsed = urlparse(url)
    if parsed.scheme != "file":
        raise ValueError(f"Not a file URL: {url}")

    if parsed.netloc and parsed.netloc.lower() != "localhost":
        path = f"//{parsed.netloc}{parsed.path}"
    else:
        path = parsed.path

    # Windows: file:///C:/Users/... → /C:/Users/… → C:/Users/…
    if path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]
    elif not (parsed.netloc and parsed.netloc.lower() != "localhost"):
        # On POSIX / local paths, normalize redundant leading slashes
        if path.startswith("//"):
            path = "/" + path.lstrip("/")

    return Path(unquote(path))


def path_to_itunes_url(path: Path) -> str:
    """Convert a local Path back to the file:// URL format iTunes uses.

    iTunes uses percent-encoded file:// URIs.  On Windows the path becomes
    file:///C:/Users/… (three slashes, forward-slashes, percent-encoded).
    """
    # Normalise to forward slashes
    posix_str = str(path).replace("\\", "/")
    if not posix_str.startswith("/"):
        # Windows drive letter — add leading slash
        posix_str = "/" + posix_str
    # Percent-encode everything except safe chars
    return "file://" + quote(posix_str, safe="/:@!$&'()*+,;=")


def import_library(xml_path: str) -> List[Track]:
    """Import tracks from iTunes library XML."""
    tracks = []
    try:
        with open(xml_path, "rb") as f:
            plist = plistlib.load(f)
    except Exception as e:
        logger.error(f"Failed to read iTunes library plist: {e}")
        return []

    tracks_dict = plist.get("Tracks")
    if not isinstance(tracks_dict, dict):
        logger.error("No 'Tracks' dictionary in iTunes library")
        return []

    for _track_id, track_info in tracks_dict.items():
        if not isinstance(track_info, dict):
            continue

        location = track_info.get("Location")
        if not location:
            continue

        try:
            file_path = itunes_url_to_path(location)
        except ValueError as e:
            logger.warning(f"Invalid file URL {location}: {e}")
            continue

        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            continue

        track = Track(file_path)
        if not track.load():
            logger.warning(f"Failed to load track: {file_path}")
            continue

        # Override with iTunes metadata where present
        _map_itunes_fields(track_info, track)
        tracks.append(track)

    logger.info(f"Imported {len(tracks)} tracks from iTunes library")
    return tracks


def _map_itunes_fields(track_info: dict, track: Track) -> None:
    """Apply iTunes plist field dict to a Track object."""
    if artist := track_info.get("Artist"):
        track.artist = str(artist)
    if album := track_info.get("Album"):
        track.album = str(album)
    if title := track_info.get("Name"):
        track.title = str(title)
    if genre := track_info.get("Genre"):
        track.genre = str(genre)
    if composer := track_info.get("Composer"):
        track.composer = str(composer)
    if grouping := track_info.get("Grouping"):
        track.grouping = str(grouping)
    if comment := track_info.get("Comments"):
        track.comment = str(comment)
    if isinstance(n := track_info.get("Track Number"), int) and n > 0:
        track.track_number = n
    if isinstance(nt := track_info.get("Track Count"), int) and nt > 0:
        track.track_total = nt
    if isinstance(d := track_info.get("Disc Number"), int) and d > 0:
        track.disc_number = d
    if isinstance(dt := track_info.get("Disc Count"), int) and dt > 0:
        track.disc_total = dt
    if isinstance(y := track_info.get("Year"), int) and y > 0:
        track.year = y
    if isinstance(b := track_info.get("BPM"), int) and b > 0:
        track.bpm = b


def _normalize_path_key(path: Path) -> str:
    """Return platform-aware path string for case-sensitive/insensitive mapping."""
    try:
        resolved = str(path.resolve())
    except Exception:
        resolved = str(path)
    return resolved.lower() if os.name == "nt" else resolved


def export_changes(tracks: List[Track], xml_path: str) -> bool:
    """Export track metadata changes back to an iTunes Library XML file.

    The function:
    1. Reads the existing iTunes XML.
    2. Builds a mapping of file path → Tracks entry using platform-aware identity.
    3. Updates every matching entry with current Track metadata, removing cleared fields.
    4. Creates a .bak backup of the original, then writes the updated XML atomically.

    Returns True on success, False on any failure.
    """
    xml_file = Path(xml_path)
    if not xml_file.exists():
        logger.error(f"iTunes XML not found: {xml_path}")
        return False

    # ── Load ──────────────────────────────────────────────────────────────
    try:
        with open(xml_file, "rb") as fh:
            plist = plistlib.load(fh)
    except Exception as e:
        logger.error(f"Failed to read iTunes library: {e}")
        return False

    tracks_dict = plist.get("Tracks")
    if not isinstance(tracks_dict, dict):
        logger.error("Malformed iTunes XML: missing 'Tracks' dictionary")
        return False

    # ── Build path→entry map ───────────────────────────────────────────────
    path_to_entry: dict[str, dict] = {}
    for entry in tracks_dict.values():
        if isinstance(entry, dict) and (loc := entry.get("Location")):
            try:
                p = itunes_url_to_path(loc)
                path_to_entry[_normalize_path_key(p)] = entry
            except Exception:
                pass

    updated = 0
    for track in tracks:
        entry = path_to_entry.get(_normalize_path_key(track.file_path))
        if entry is None:
            logger.debug(f"Track not found in iTunes XML: {track.file_path.name}")
            continue

        # Write back every field that iTunes supports; remove cleared optional fields
        entry["Name"] = track.title
        entry["Artist"] = track.artist
        entry["Album"] = track.album
        entry["Genre"] = track.genre

        if track.composer:
            entry["Composer"] = track.composer
        elif "Composer" in entry:
            del entry["Composer"]

        if track.grouping:
            entry["Grouping"] = track.grouping
        elif "Grouping" in entry:
            del entry["Grouping"]

        if track.comment:
            entry["Comments"] = track.comment
        elif "Comments" in entry:
            del entry["Comments"]

        if track.track_number > 0:
            entry["Track Number"] = track.track_number
        elif "Track Number" in entry:
            del entry["Track Number"]

        if track.track_total > 0:
            entry["Track Count"] = track.track_total
        elif "Track Count" in entry:
            del entry["Track Count"]

        if track.disc_number > 0:
            entry["Disc Number"] = track.disc_number
        elif "Disc Number" in entry:
            del entry["Disc Number"]

        if track.disc_total > 0:
            entry["Disc Count"] = track.disc_total
        elif "Disc Count" in entry:
            del entry["Disc Count"]

        if track.year > 0:
            entry["Year"] = track.year
        elif "Year" in entry:
            del entry["Year"]

        if track.bpm > 0:
            entry["BPM"] = track.bpm
        elif "BPM" in entry:
            del entry["BPM"]

        updated += 1

    if updated == 0:
        logger.warning("No tracks matched in iTunes XML — nothing to export")
        return False

    # ── Require successful backup before touching the source ──────────────
    backup = xml_file.with_suffix(".bak")
    try:
        shutil.copy2(xml_file, backup)
        logger.info(f"iTunes XML backup saved to {backup}")
    except Exception as e:
        logger.error(f"Could not create required backup before export: {e}")
        return False

    # ── Write updated XML safely via temporary file and atomic replace ────
    import tempfile
    import os
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=xml_file.parent,
            delete=False,
            prefix=f"{xml_file.stem}_",
            suffix=".tmp",
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            plistlib.dump(plist, tmp_file, fmt=plistlib.FMT_XML)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())

        os.replace(tmp_path, xml_file)
        logger.info(f"Exported changes for {updated} track(s) to {xml_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write iTunes XML atomically: {e}")
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        return False
