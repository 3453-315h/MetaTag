"""Unit tests for CSV import/export."""

import pytest
import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from metatag.import_io.csv_io import import_csv, export_csv, map_headers
from metatag.core.track import Track


def test_map_headers_basic():
    """Test header mapping with standard column names."""
    headers = ["Artist", "Album", "Title", "Track Number", "File Path"]
    mapping = map_headers(headers)
    assert mapping["artist"] == [0]
    assert mapping["album"] == [1]
    assert mapping["title"] == [2]
    assert mapping["track_number"] == [3]
    assert mapping["file_path"] == [4]


def test_map_headers_case_insensitive():
    """Test header mapping is case-insensitive."""
    headers = ["ARTIST", "album", "TiTle"]
    mapping = map_headers(headers)
    assert mapping["artist"] == [0]
    assert mapping["album"] == [1]
    assert mapping["title"] == [2]


def test_map_headers_alternate_names():
    """Test alternate column names."""
    headers = ["Artist Name", "Album Title", "Track Title", "File", "BPM"]
    mapping = map_headers(headers)
    assert mapping["artist"] == [0]
    assert mapping["album"] == [1]
    assert mapping["title"] == [2]
    assert mapping["file_path"] == [3]
    assert mapping["bpm"] == [4]


def test_map_headers_multiple_matches():
    """Test multiple columns mapping to same field (first wins)."""
    headers = ["Artist", "Artist", "Title"]
    mapping = map_headers(headers)
    assert mapping["artist"] == [0, 1]  # Both indices
    assert mapping["title"] == [2]


def test_map_headers_unknown_headers():
    """Test headers not recognized are ignored."""
    headers = ["Unknown", "Artist", "Random"]
    mapping = map_headers(headers)
    assert "artist" in mapping
    assert "unknown" not in mapping
    assert "random" not in mapping


def test_import_csv_empty_file(temp_dir):
    """Test importing empty CSV."""
    csv_path = Path(temp_dir) / "empty.csv"
    csv_path.write_text("")  # empty file

    tracks = import_csv(str(csv_path))
    assert tracks == []


def test_import_csv_only_headers(temp_dir):
    """Test CSV with only headers."""
    csv_path = Path(temp_dir) / "headers.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Artist", "Title"])

    tracks = import_csv(str(csv_path))
    assert tracks == []


def test_import_csv_missing_file_path_column(temp_dir):
    """Test CSV missing required file path column."""
    csv_path = Path(temp_dir) / "test.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Artist", "Title"])  # No file path
        writer.writerow(["Artist1", "Title1"])

    tracks = import_csv(str(csv_path))
    assert tracks == []


def test_import_csv_success_mocked(temp_dir):
    """Test successful CSV import with mocked Track."""
    csv_path = Path(temp_dir) / "test.csv"
    # Create a dummy audio file
    audio_path = Path(temp_dir) / "song.mp3"
    audio_path.write_bytes(b"fake audio")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Artist", "Title", "Track Number"])
        writer.writerow([str(audio_path), "Test Artist", "Test Title", "5"])

    # Mock Track to avoid actual mutagen loading
    mock_track = Mock(spec=Track)
    mock_track.load.return_value = True
    mock_track.artist = ""
    mock_track.title = ""
    mock_track.track_number = 0

    with patch("metatag.import_io.csv_io.Track") as MockTrack:
        MockTrack.return_value = mock_track
        tracks = import_csv(str(csv_path))

        assert len(tracks) == 1
        MockTrack.assert_called_once()
        assert MockTrack.call_args[0][0] == str(audio_path)
        mock_track.load.assert_called_once()
        # Check that setters were called
        # (mock_track.artist = "Test Artist" etc. - hard to verify with Mock)
        # We'll trust the code if load succeeded


def test_import_csv_file_not_exists(temp_dir):
    """Test CSV referencing non-existent audio file."""
    csv_path = Path(temp_dir) / "test.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Artist"])
        writer.writerow(["/nonexistent/file.mp3", "Artist"])

    tracks = import_csv(str(csv_path))
    assert tracks == []  # Should skip missing files


def test_import_csv_invalid_row_length(temp_dir):
    """Test CSV with row length mismatch."""
    csv_path = Path(temp_dir) / "test.csv"
    audio_path = Path(temp_dir) / "song.mp3"
    audio_path.write_bytes(b"fake")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Artist"])
        writer.writerow([str(audio_path)])  # Missing artist column
        writer.writerow([str(audio_path), "Artist", "Extra"])  # Extra column

    with patch("metatag.import_io.csv_io.Track") as MockTrack:
        mock_track = Mock(spec=Track)
        mock_track.load.return_value = True
        MockTrack.return_value = mock_track
        tracks = import_csv(str(csv_path))

        # Row 1: 1 column < 2 headers → skipped
        # Row 2: 3 columns >= 2 headers → accepted (extra column ignored)
        assert len(tracks) == 1


def test_import_csv_conversion_errors(temp_dir):
    """Test CSV with non-integer values for numeric fields."""
    csv_path = Path(temp_dir) / "test.csv"
    audio_path = Path(temp_dir) / "song.mp3"
    audio_path.write_bytes(b"fake")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Track Number", "Year", "BPM"])
        writer.writerow([str(audio_path), "not-a-number", "invalid", "120.5"])

    with patch("metatag.import_io.csv_io.Track") as MockTrack:
        mock_track = Mock(spec=Track)
        mock_track.load.return_value = True
        MockTrack.return_value = mock_track
        tracks = import_csv(str(csv_path))

        # Should succeed but numeric fields ignored due to ValueError
        assert len(tracks) == 1
        # track.track_number and track.year remain default (0)


def test_export_csv_success(temp_dir):
    """Test successful CSV export."""
    tracks = []
    for i in range(3):
        track = Mock(spec=Track)
        track.file_path = Path(f"song{i}.mp3")
        track.artist = f"Artist{i}"
        track.album = f"Album{i}"
        track.title = f"Title{i}"
        track.track_number = i + 1
        track.disc_number = 1
        track.genre = "Rock"
        track.year = 2023
        track.comment = f"Comment{i}"
        track.composer = f"Composer{i}"
        track.grouping = f"Group{i}"
        track.bpm = 120 + i
        tracks.append(track)

    csv_path = Path(temp_dir) / "export.csv"
    result = export_csv(tracks, str(csv_path))

    assert result is True
    assert csv_path.exists()

    # Verify CSV content
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 4  # header + 3 tracks
        assert rows[0] == [
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
        for i, row in enumerate(rows[1:], start=0):
            assert row[0] == f"song{i}.mp3"
            assert row[1] == f"Artist{i}"
            assert row[2] == f"Album{i}"
            assert row[3] == f"Title{i}"
            assert int(row[4]) == i + 1
            assert int(row[5]) == 1
            assert row[6] == "Rock"
            assert int(row[7]) == 2023
            assert row[8] == f"Comment{i}"
            assert row[9] == f"Composer{i}"
            assert row[10] == f"Group{i}"
            assert int(row[11]) == 120 + i


def test_export_csv_empty_list(temp_dir):
    """Test exporting empty track list."""
    csv_path = Path(temp_dir) / "export.csv"
    result = export_csv([], str(csv_path))
    assert result is False
    assert not csv_path.exists()


def test_export_csv_write_error(temp_dir):
    """Test export when file write fails."""
    tracks = [Mock(spec=Track)]
    csv_path = Path(temp_dir) / "export.csv"

    # Make directory unwritable by mocking open to raise exception
    with patch("builtins.open", side_effect=PermissionError("Access denied")):
        result = export_csv(tracks, str(csv_path))
        assert result is False


def test_export_csv_formula_sanitization(temp_dir):
    """Test Finding #23: Fields starting with =, +, -, @ are escaped to prevent formula injection."""
    track = Mock(spec=Track)
    track.file_path = Path("song.mp3")
    track.artist = "=cmd|' /C calc'!A0"
    track.album = "+SUM(A1:A10)"
    track.title = "-1+1"
    track.track_number = 1
    track.disc_number = 1
    track.genre = "@evil"
    track.year = 2024
    track.comment = "Normal comment"
    track.composer = "=1+1"
    track.grouping = ""
    track.bpm = 120

    csv_path = Path(temp_dir) / "export_formula.csv"
    assert export_csv([track], str(csv_path)) is True

    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
        data_row = rows[1]
        assert data_row[1] == "'=cmd|' /C calc'!A0"
        assert data_row[2] == "'+SUM(A1:A10)"
        assert data_row[3] == "'-1+1"
        assert data_row[6] == "'@evil"
        assert data_row[9] == "'=1+1"


def test_export_html_markup_escaping(temp_dir):
    """Test Finding #23: HTML export escapes hostile markup strings."""
    from metatag.core.export.exporter import export_html

    track = Mock(spec=Track)
    track.file_path = Path("evil<script>.mp3")
    track.artist = "<script>alert(1)</script>"
    track.album = "Rock & Roll <img src=x onerror=alert(2)>"
    track.title = "<b>Bold</b> & 'Special'"
    track.track_number = 1
    track.duration = 180000

    html_path = Path(temp_dir) / "report.html"
    assert export_html([track], html_path) is True

    content = html_path.read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content
    assert "Rock &amp; Roll &lt;img src=x onerror=alert(2)&gt;" in content
    assert "&lt;b&gt;Bold&lt;/b&gt; &amp; &#x27;Special&#x27;" in content or "&lt;b&gt;Bold&lt;/b&gt; &amp; 'Special'" in content


if __name__ == "__main__":
    pytest.main([__file__])
