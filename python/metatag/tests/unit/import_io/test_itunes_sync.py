"""Unit tests for iTunes sync."""

import pytest
import plistlib
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from metatag.import_io.itunes_sync import (
    itunes_url_to_path,
    import_library,
    export_changes,
)


def test_itunes_url_to_path_windows():
    """Convert Windows file:// URL to Path."""
    # Standard Windows path
    url = "file:///C:/Users/Test/Music/song.mp3"
    result = itunes_url_to_path(url)
    assert result == Path("C:/Users/Test/Music/song.mp3")

    # With spaces and URL encoding
    url = "file:///C:/My%20Music/song%20title.mp3"
    result = itunes_url_to_path(url)
    assert result == Path("C:/My Music/song title.mp3")


def test_itunes_url_to_path_unix():
    """Convert Unix file:// URL to Path."""
    url = "file:///home/user/music/song.mp3"
    result = itunes_url_to_path(url)
    assert result == Path("/home/user/music/song.mp3")


def test_itunes_url_to_path_network():
    """Convert network file:// URL."""
    url = "file://server/share/music/song.mp3"
    result = itunes_url_to_path(url)
    # path starts with '//server/share/...'
    assert result == Path("//server/share/music/song.mp3")


def test_itunes_url_to_path_invalid_scheme():
    """Raise ValueError for non-file URL."""
    url = "http://example.com/song.mp3"
    with pytest.raises(ValueError, match="Not a file URL"):
        itunes_url_to_path(url)


def test_import_library_file_not_found():
    """Test import when XML file doesn't exist."""
    result = import_library("/nonexistent/path.xml")
    assert result == []


def test_import_library_invalid_plist():
    """Test import with invalid plist."""
    mock_data = b"not a plist"
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("plistlib.load", side_effect=plistlib.InvalidFileException):
            result = import_library("dummy.xml")
            assert result == []


def test_import_library_no_tracks_dict():
    """Test iTunes XML missing Tracks dictionary."""
    mock_plist = {"Playlists": []}
    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            result = import_library("dummy.xml")
            assert result == []


def test_import_library_empty_tracks():
    """Test iTunes XML with empty Tracks."""
    mock_plist = {"Tracks": {}}
    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            result = import_library("dummy.xml")
            assert result == []


def test_import_library_success_mocked(temp_dir):
    """Test successful import with mocked files."""
    # Create a dummy audio file
    audio_path = Path(temp_dir) / "song.mp3"
    audio_path.write_bytes(b"fake audio")

    # Build mock iTunes plist
    mock_plist = {
        "Tracks": {
            "1": {
                "Location": f"file:///{audio_path.as_posix().replace(':', ':/')}",
                "Artist": "Test Artist",
                "Album": "Test Album",
                "Name": "Test Title",
                "Genre": "Rock",
                "Composer": "Test Composer",
                "Grouping": "Test Group",
                "Comments": "Test Comment",
                "Track Number": 5,
                "Disc Number": 1,
                "Year": 2023,
                "BPM": 120,
            }
        }
    }

    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            with patch("metatag.import_io.itunes_sync.Track") as MockTrack:
                mock_track = Mock()
                mock_track.load.return_value = True
                mock_track.artist = ""
                mock_track.album = ""
                mock_track.title = ""
                mock_track.genre = ""
                mock_track.composer = ""
                mock_track.grouping = ""
                mock_track.comment = ""
                mock_track.track_number = 0
                mock_track.disc_number = 0
                mock_track.year = 0
                mock_track.bpm = 0
                MockTrack.return_value = mock_track

                tracks = import_library("dummy.xml")

                assert len(tracks) == 1
                MockTrack.assert_called_once_with(audio_path)
                mock_track.load.assert_called_once()
                # Check setters were called with correct values
                assert mock_track.artist == "Test Artist"
                assert mock_track.album == "Test Album"
                assert mock_track.title == "Test Title"
                assert mock_track.genre == "Rock"
                assert mock_track.composer == "Test Composer"
                assert mock_track.grouping == "Test Group"
                assert mock_track.comment == "Test Comment"
                assert mock_track.track_number == 5
                assert mock_track.disc_number == 1
                assert mock_track.year == 2023
                assert mock_track.bpm == 120


def test_import_library_missing_location():
    """Test track entry missing Location."""
    mock_plist = {"Tracks": {"1": {"Artist": "Artist"}}}  # No Location
    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            tracks = import_library("dummy.xml")
            assert tracks == []


def test_import_library_invalid_location():
    """Test track entry with invalid file URL."""
    mock_plist = {"Tracks": {"1": {"Location": "http://example.com/file.mp3"}}}
    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            tracks = import_library("dummy.xml")
            assert tracks == []


def test_import_library_file_not_exists():
    """Test track where file doesn't exist."""
    mock_plist = {"Tracks": {"1": {"Location": "file:///C:/nonexistent/song.mp3"}}}
    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            tracks = import_library("dummy.xml")
            assert tracks == []


def test_import_library_track_load_fails(temp_dir):
    """Test track where Track.load() fails."""
    audio_path = Path(temp_dir) / "song.mp3"
    audio_path.write_bytes(b"fake")

    mock_plist = {
        "Tracks": {
            "1": {"Location": f"file:///{audio_path.as_posix().replace(':', ':/')}"}
        }
    }

    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            with patch("metatag.import_io.itunes_sync.Track") as MockTrack:
                mock_track = Mock()
                mock_track.load.return_value = False
                MockTrack.return_value = mock_track

                tracks = import_library("dummy.xml")
                assert tracks == []


def test_import_library_non_dict_track_info():
    """Test track entry that is not a dict."""
    mock_plist = {"Tracks": {"1": "not a dict"}}
    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            tracks = import_library("dummy.xml")
            assert tracks == []


def test_import_library_non_int_numeric_fields():
    """Test numeric fields with non-integer values."""
    audio_path = Path("/dummy/song.mp3")
    mock_plist = {
        "Tracks": {
            "1": {
                "Location": f"file:///{audio_path.as_posix().replace(':', ':/')}",
                "Track Number": "five",  # string
                "Disc Number": 0,  # zero (should be ignored)
                "Year": 2023.5,  # float (should be ignored)
                "BPM": "120",  # string (should be ignored)
            }
        }
    }

    with patch("builtins.open", mock_open(read_data=b"")):
        with patch("plistlib.load", return_value=mock_plist):
            with patch("metatag.import_io.itunes_sync.Track") as MockTrack:
                mock_track = Mock()
                mock_track.load.return_value = True
                mock_track.track_number = 0
                mock_track.disc_number = 0
                mock_track.year = 0
                mock_track.bpm = 0
                MockTrack.return_value = mock_track
                with patch("pathlib.Path.exists", return_value=True):
                    tracks = import_library("dummy.xml")
                    assert len(tracks) == 1
                    # Numeric fields should remain default (0) because:
                    # - "five" not int -> ignored
                    # - 0 not >0 -> ignored
                    # - 2023.5 not int -> ignored
                    # - "120" not int -> ignored


def test_export_changes_missing_xml():
    """export_changes returns False when the XML file does not exist."""
    result = export_changes([], "/nonexistent/iTunes Library.xml")
    assert result is False


def test_export_changes_round_trip(temp_dir):
    """export_changes writes updated metadata back into the iTunes XML."""
    # Build a minimal iTunes Library XML
    audio_file = Path(temp_dir) / "song.mp3"
    audio_file.write_bytes(b"fake")

    from metatag.import_io.itunes_sync import path_to_itunes_url
    location_url = path_to_itunes_url(audio_file)

    plist_data = {
        "Tracks": {
            "1": {
                "Location": location_url,
                "Name": "Old Title",
                "Artist": "Old Artist",
                "Album": "Old Album",
                "Genre": "",
            }
        }
    }
    xml_path = Path(temp_dir) / "iTunes Library.xml"
    with open(xml_path, "wb") as fh:
        plistlib.dump(plist_data, fh, fmt=plistlib.FMT_XML)

    # Create a track mock with updated metadata
    mock_track = Mock()
    mock_track.file_path = audio_file
    mock_track.title = "New Title"
    mock_track.artist = "New Artist"
    mock_track.album = "New Album"
    mock_track.genre = "Rock"
    mock_track.composer = ""
    mock_track.grouping = ""
    mock_track.comment = ""
    mock_track.track_number = 3
    mock_track.track_total = 10
    mock_track.disc_number = 1
    mock_track.disc_total = 2
    mock_track.year = 2024
    mock_track.bpm = 128

    result = export_changes([mock_track], str(xml_path))
    assert result is True

    # Verify the backup was created
    assert (Path(temp_dir) / "iTunes Library.bak").exists()

    # Verify the XML was updated
    with open(xml_path, "rb") as fh:
        updated = plistlib.load(fh)

    entry = updated["Tracks"]["1"]
    assert entry["Name"]   == "New Title"
    assert entry["Artist"] == "New Artist"
    assert entry["Album"]  == "New Album"
    assert entry["Genre"]  == "Rock"
    assert entry["Track Number"] == 3
    assert entry["Year"] == 2024
    assert entry["BPM"]  == 128


if __name__ == "__main__":
    pytest.main([__file__])
