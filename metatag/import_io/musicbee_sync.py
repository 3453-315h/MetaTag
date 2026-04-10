"""MusicBee library import."""

import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

from ..core.track import Track

logger = logging.getLogger(__name__)


def map_columns(column_names: List[str]) -> Dict[str, int]:
    """Map column names to column indices for track attributes."""
    mapping = {}
    for idx, col in enumerate(column_names):
        col_lower = col.lower().strip()
        if col_lower in ("artist", "artist name"):
            mapping["artist"] = idx
        elif col_lower in ("album", "album title"):
            mapping["album"] = idx
        elif col_lower in ("title", "track title", "name"):
            mapping["title"] = idx
        elif col_lower in ("track", "track number", "tracknumber"):
            mapping["track_number"] = idx
        elif col_lower in ("disc", "disc number", "discnumber"):
            mapping["disc_number"] = idx
        elif col_lower == "genre":
            mapping["genre"] = idx
        elif col_lower == "year":
            mapping["year"] = idx
        elif col_lower == "comment":
            mapping["comment"] = idx
        elif col_lower == "composer":
            mapping["composer"] = idx
        elif col_lower == "grouping":
            mapping["grouping"] = idx
        elif col_lower == "bpm":
            mapping["bpm"] = idx
        elif col_lower in ("file", "file path", "path", "filepath", "location"):
            mapping["file_path"] = idx
    return mapping


def import_library(db_path: str) -> List[Track]:
    """Import tracks from MusicBee SQLite library."""
    tracks = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"Failed to connect to MusicBee database: {e}")
        return []

    try:
        # Get column names
        logger.debug("Getting column names")
        cursor.execute("PRAGMA table_info(Tracks);")
        columns = cursor.fetchall()
        if not columns:
            logger.error("No columns found in Tracks table")
            return []
        column_names = [col[1] for col in columns]  # column name is second field

        mapping = map_columns(column_names)
        logger.debug(f"Column names: {column_names}")
        logger.debug(f"Mapping: {mapping}")
        if "file_path" not in mapping:
            logger.error("No file path column found in Tracks table")
            return []

        # Build SELECT query with column order as they appear
        logger.debug("Executing SELECT")
        cursor.execute("SELECT * FROM Tracks")
        logger.debug("Fetching rows")
        rows = cursor.fetchall()
        logger.debug(f"Rows: {rows}")
        logger.debug(f"Row count: {len(rows)}")

        for row in rows:
            file_path = row[mapping["file_path"]]
            if not file_path:
                continue
            file_path = str(file_path).strip()
            if not file_path:
                continue

            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File does not exist: {path}")
                continue

            track = Track(path)
            if not track.load():
                logger.warning(f"Failed to load track: {path}")
                continue

            # Apply metadata
            if "artist" in mapping:
                val = row[mapping["artist"]]
                if val:
                    track.artist = str(val).strip()
            if "album" in mapping:
                val = row[mapping["album"]]
                if val:
                    track.album = str(val).strip()
            if "title" in mapping:
                val = row[mapping["title"]]
                if val:
                    track.title = str(val).strip()
            if "track_number" in mapping:
                val = row[mapping["track_number"]]
                if val:
                    try:
                        track.track_number = int(val)
                    except (ValueError, TypeError):
                        pass
            if "disc_number" in mapping:
                val = row[mapping["disc_number"]]
                if val:
                    try:
                        track.disc_number = int(val)
                    except (ValueError, TypeError):
                        pass
            if "genre" in mapping:
                val = row[mapping["genre"]]
                if val:
                    track.genre = str(val).strip()
            if "year" in mapping:
                val = row[mapping["year"]]
                if val:
                    try:
                        track.year = int(val)
                    except (ValueError, TypeError):
                        pass
            if "comment" in mapping:
                val = row[mapping["comment"]]
                if val:
                    track.comment = str(val).strip()
            if "composer" in mapping:
                val = row[mapping["composer"]]
                if val:
                    track.composer = str(val).strip()
            if "grouping" in mapping:
                val = row[mapping["grouping"]]
                if val:
                    track.grouping = str(val).strip()
            if "bpm" in mapping:
                val = row[mapping["bpm"]]
                if val:
                    try:
                        track.bpm = int(val)
                    except (ValueError, TypeError):
                        pass

            tracks.append(track)

    except Exception as e:
        logger.error(f"Error reading MusicBee library: {e}")
        return []
    finally:
        conn.close()

    logger.info(f"Imported {len(tracks)} tracks from MusicBee library")
    return tracks


def export_changes(tracks: List[Track]) -> bool:
    """Export changes back to MusicBee library (not implemented)."""
    logger.warning(
        "MusicBee export is not implemented. Changes were not exported to MusicBee library."
    )
    # Implementation would require:
    # 1. Updating the SQLite database with new metadata
    # 2. Handling concurrency and database locks
    # This is complex and error-prone, so we'll leave it unimplemented for now
    return False
