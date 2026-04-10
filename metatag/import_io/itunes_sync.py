"""iTunes library import/export."""

import logging
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

    if parsed.netloc:
        path = f"//{parsed.netloc}{parsed.path}"
    else:
        path = parsed.path

    # Windows: file:///C:/Users/... → /C:/Users/… → C:/Users/…
    if path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]

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
    if isinstance(d := track_info.get("Disc Number"), int) and d > 0:
        track.disc_number = d
    if isinstance(y := track_info.get("Year"), int) and y > 0:
        track.year = y
    if isinstance(b := track_info.get("BPM"), int) and b > 0:
        track.bpm = b


def export_changes(tracks: List[Track], xml_path: str) -> bool:
    """Export track metadata changes back to an iTunes Library XML file.

    The function:
    1. Reads the existing iTunes XML.
    2. Builds a mapping of file:// URL → Tracks entry.
    3. Updates every matching entry with current Track metadata.
    4. Creates a .bak backup of the original, then writes the updated XML.

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

    # ── Build URL→entry map ───────────────────────────────────────────────
    # Key = normalised file URL string; value = the mutable plist sub-dict
    url_to_entry: dict[str, dict] = {}
    for entry in tracks_dict.values():
        if isinstance(entry, dict) and (loc := entry.get("Location")):
            # Normalise to lower-case for case-insensitive path matching
            url_to_entry[loc.lower()] = entry

    updated = 0
    for track in tracks:
        url = path_to_itunes_url(track.file_path)
        entry = url_to_entry.get(url.lower())
        if entry is None:
            logger.debug(f"Track not found in iTunes XML: {track.file_path.name}")
            continue

        # Write back every field that iTunes supports
        entry["Name"]    = track.title
        entry["Artist"]  = track.artist
        entry["Album"]   = track.album
        entry["Genre"]   = track.genre
        if track.composer:
            entry["Composer"] = track.composer
        if track.grouping:
            entry["Grouping"] = track.grouping
        if track.comment:
            entry["Comments"] = track.comment
        if track.track_number > 0:
            entry["Track Number"] = track.track_number
        if track.track_total > 0:
            entry["Track Count"] = track.track_total
        if track.disc_number > 0:
            entry["Disc Number"] = track.disc_number
        if track.disc_total > 0:
            entry["Disc Count"] = track.disc_total
        if track.year > 0:
            entry["Year"] = track.year
        if track.bpm > 0:
            entry["BPM"] = track.bpm

        updated += 1

    if updated == 0:
        logger.warning("No tracks matched in iTunes XML — nothing to export")
        return False

    # ── Backup original ───────────────────────────────────────────────────
    backup = xml_file.with_suffix(".bak")
    try:
        shutil.copy2(xml_file, backup)
        logger.info(f"iTunes XML backup saved to {backup}")
    except Exception as e:
        logger.warning(f"Could not create backup: {e}")

    # ── Write updated XML ─────────────────────────────────────────────────
    try:
        with open(xml_file, "wb") as fh:
            plistlib.dump(plist, fh, fmt=plistlib.FMT_XML)
        logger.info(f"Exported changes for {updated} track(s) to {xml_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write iTunes XML: {e}")
        return False
