"""CSV import/export."""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional
from ..core.track import Track

logger = logging.getLogger(__name__)


def import_csv(csv_path: str) -> List[Track]:
    """Import tracks from CSV file."""
    tracks = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            # Use csv.reader to handle quoted fields
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                return []

            # Map header indices
            mapping = map_headers(headers)
            if "file_path" not in mapping:
                logger.error("CSV missing file path column")
                return []

            for row_num, row in enumerate(reader, start=2):
                if len(row) < len(headers):
                    logger.warning(
                        f"CSV line {row_num} has {len(row)} fields but expected {len(headers)}, skipping"
                    )
                    continue

                file_path = row[mapping["file_path"][0]].strip()
                if not file_path:
                    logger.warning(f"CSV line {row_num} has empty file path, skipping")
                    continue

                if not Path(file_path).exists():
                    logger.warning(f"CSV file does not exist: {file_path}, skipping")
                    continue

                track = Track(file_path)
                if not track.load():
                    logger.warning(f"Failed to load track: {file_path}, skipping")
                    continue

                # Apply metadata
                if "artist" in mapping:
                    track.artist = row[mapping["artist"][0]].strip()
                if "album" in mapping:
                    track.album = row[mapping["album"][0]].strip()
                if "title" in mapping:
                    track.title = row[mapping["title"][0]].strip()
                if "track_number" in mapping:
                    try:
                        track.track_number = int(row[mapping["track_number"][0]])
                    except ValueError:
                        pass
                if "disc_number" in mapping:
                    try:
                        track.disc_number = int(row[mapping["disc_number"][0]])
                    except ValueError:
                        pass
                if "genre" in mapping:
                    track.genre = row[mapping["genre"][0]].strip()
                if "year" in mapping:
                    try:
                        track.year = int(row[mapping["year"][0]])
                    except ValueError:
                        pass
                if "comment" in mapping:
                    track.comment = row[mapping["comment"][0]].strip()
                if "composer" in mapping:
                    track.composer = row[mapping["composer"][0]].strip()
                if "grouping" in mapping:
                    track.grouping = row[mapping["grouping"][0]].strip()
                if "bpm" in mapping:
                    try:
                        track.bpm = int(row[mapping["bpm"][0]])
                    except ValueError:
                        pass

                tracks.append(track)

    except Exception as e:
        logger.error(f"Failed to import CSV: {e}")
        return []

    return tracks


def map_headers(headers: List[str]) -> Dict[str, List[int]]:
    """Map header names to column indices."""
    mapping = {}
    for idx, header in enumerate(headers):
        h = header.lower().strip()
        if h in ("artist", "artist name"):
            mapping.setdefault("artist", []).append(idx)
        elif h in ("album", "album title"):
            mapping.setdefault("album", []).append(idx)
        elif h in ("title", "track title"):
            mapping.setdefault("title", []).append(idx)
        elif h in ("track", "track number"):
            mapping.setdefault("track_number", []).append(idx)
        elif h in ("disc", "disc number"):
            mapping.setdefault("disc_number", []).append(idx)
        elif h == "genre":
            mapping.setdefault("genre", []).append(idx)
        elif h == "year":
            mapping.setdefault("year", []).append(idx)
        elif h == "comment":
            mapping.setdefault("comment", []).append(idx)
        elif h == "composer":
            mapping.setdefault("composer", []).append(idx)
        elif h == "grouping":
            mapping.setdefault("grouping", []).append(idx)
        elif h == "bpm":
            mapping.setdefault("bpm", []).append(idx)
        elif h in ("file", "file path", "path"):
            mapping.setdefault("file_path", []).append(idx)
    return mapping


def export_csv(tracks: List[Track], csv_path: str) -> bool:
    """Export tracks to CSV file."""
    if not tracks:
        return False

    try:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(
                [
                    "File Path",
                    "Artist",
                    "Album",
                    "Title",
                    "Track Number",
                    "Disc Number",
                    "Genre",
                    "Year",
                    "Comment",
                    "Composer",
                    "Grouping",
                    "BPM",
                ]
            )
            for track in tracks:
                writer.writerow(
                    [
                        str(track.file_path),
                        track.artist,
                        track.album,
                        track.title,
                        track.track_number,
                        track.disc_number,
                        track.genre,
                        track.year,
                        track.comment,
                        track.composer,
                        track.grouping,
                        track.bpm,
                    ]
                )
        return True
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        return False
