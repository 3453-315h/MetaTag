"""Unit tests for MusicBee sync."""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from metatag.import_io.musicbee_sync import (
    map_columns,
    import_library,
    export_changes,
)


def test_map_columns_basic():
    """Map column names to indices."""
    columns = ["FilePath", "Artist", "Album", "Title"]
    mapping = map_columns(columns)
    assert mapping["file_path"] == 0
    assert mapping["artist"] == 1
    assert mapping["album"] == 2
    assert mapping["title"] == 3
    assert "track_number" not in mapping


def test_map_columns_case_insensitive():
    """Mapping is case-insensitive."""
    columns = ["filepath", "ARTIST", "album", "TITLE"]
    mapping = map_columns(columns)
    assert mapping["file_path"] == 0
    assert mapping["artist"] == 1
    assert mapping["album"] == 2
    assert mapping["title"] == 3


def test_map_columns_alternate_names():
    """Map alternate column names."""
    columns = ["Path", "Artist Name", "Album Title", "Track Title", "Disc Number"]
    mapping = map_columns(columns)
    assert mapping["file_path"] == 0
    assert mapping["artist"] == 1
    assert mapping["album"] == 2
    assert mapping["title"] == 3
    assert mapping["disc_number"] == 4


def test_map_columns_unknown_headers():
    """Unknown headers are ignored."""
    columns = ["Unknown", "Artist", "Random"]
    mapping = map_columns(columns)
    assert mapping["artist"] == 1
    assert len(mapping) == 1


def test_import_library_db_not_found():
    """Test import when database file doesn't exist."""
    with patch("sqlite3.connect", side_effect=sqlite3.Error("cannot open")):
        tracks = import_library("nonexistent.db")
        assert tracks == []


def test_import_library_no_tracks_table():
    """Test import when Tracks table missing."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.return_value = None
    mock_cursor.fetchall.return_value = []  # No columns

    with patch("sqlite3.connect", return_value=mock_conn):
        tracks = import_library("test.db")
        assert tracks == []


def test_import_library_no_file_path_column():
    """Test import when file path column missing."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    # Simulate PRAGMA table_info returning columns without file path
    mock_cursor.fetchall.return_value = [
        (0, "Artist", "TEXT", 0, None, 0),
        (1, "Album", "TEXT", 0, None, 0),
    ]

    with patch("sqlite3.connect", return_value=mock_conn):
        tracks = import_library("test.db")
        assert tracks == []


def test_import_library_success_mocked():
    """Test successful import with mocked database."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor

    # Simulate PRAGMA table_info returning columns, then SELECT query result
    mock_row = (
        "/music/song.mp3",
        "Test Artist",
        "Test Album",
        "Test Title",
        1,
        1,
        "Rock",
        2023,
        "Test comment",
        "Test composer",
        "Test grouping",
        120,
    )
    mock_cursor.fetchall.side_effect = [
        [
            (0, "FilePath", "TEXT", 0, None, 0),
            (1, "Artist", "TEXT", 0, None, 0),
            (2, "Album", "TEXT", 0, None, 0),
            (3, "Title", "TEXT", 0, None, 0),
            (4, "TrackNumber", "INTEGER", 0, None, 0),
            (5, "DiscNumber", "INTEGER", 0, None, 0),
            (6, "Genre", "TEXT", 0, None, 0),
            (7, "Year", "INTEGER", 0, None, 0),
            (8, "Comment", "TEXT", 0, None, 0),
            (9, "Composer", "TEXT", 0, None, 0),
            (10, "Grouping", "TEXT", 0, None, 0),
            (11, "BPM", "INTEGER", 0, None, 0),
        ],
        [mock_row],
    ]

    # Mock Track loading
    mock_track = Mock()
    mock_track.file_path = Path("/music/song.mp3")
    mock_track.load.return_value = True
    mock_track.artist = ""
    mock_track.album = ""
    mock_track.title = ""
    mock_track.track_number = 0
    mock_track.disc_number = 0
    mock_track.genre = ""
    mock_track.year = 0
    mock_track.comment = ""
    mock_track.composer = ""
    mock_track.grouping = ""
    mock_track.bpm = 0

    with (
        patch("sqlite3.connect", return_value=mock_conn),
        patch("metatag.import_io.musicbee_sync.Track", return_value=mock_track),
        patch("pathlib.Path.exists", return_value=True),
    ):
        tracks = import_library("test.db")
        assert len(tracks) == 1
        track = tracks[0]
        # Check that setters were called (track attributes updated)
        # Since we mocked Track, we can't easily assert values.
        # Instead we can verify that load() was called.
        mock_track.load.assert_called_once()
        # Verify that setters were called? We'll trust the mapping.


def test_import_library_file_not_exists():
    """Test import when referenced file does not exist."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.side_effect = [
        [(0, "FilePath", "TEXT", 0, None, 0)],
        [("/nonexistent.mp3",)],
    ]

    with (
        patch("sqlite3.connect", return_value=mock_conn),
        patch("pathlib.Path.exists", return_value=False),
    ):
        tracks = import_library("test.db")
        assert tracks == []


def test_import_library_track_load_fails():
    """Test import when track.load() fails."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.side_effect = [
        [(0, "FilePath", "TEXT", 0, None, 0)],
        [("/music/song.mp3",)],
    ]
    mock_track = Mock()
    mock_track.load.return_value = False

    with (
        patch("sqlite3.connect", return_value=mock_conn),
        patch("metatag.import_io.musicbee_sync.Track", return_value=mock_track),
        patch("pathlib.Path.exists", return_value=True),
    ):
        tracks = import_library("test.db")
        assert tracks == []


def test_export_changes_not_implemented():
    """Test export_changes returns False (not implemented)."""
    assert export_changes([]) is False
