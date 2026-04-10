"""Unit tests for rename_utils."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from metatag.utils.rename_utils import (
    generate_filename,
    rename_track,
    rename_tracks,
)
from metatag.core.track import Track


def create_mock_track(**kwargs):
    """Create a mock Track with default values."""
    track = Mock(spec=Track)
    # Default values
    track.artist = ""
    track.album = ""
    track.title = ""
    track.track_number = 0
    track.disc_number = 0
    track.genre = ""
    track.year = 0
    track.comment = ""
    track.composer = ""
    track.grouping = ""
    track.bpm = 0
    track.file_path = Path("song.mp3")
    # Override with any kwargs
    for key, value in kwargs.items():
        setattr(track, key, value)
    return track


def test_generate_filename_basic():
    """Test basic filename generation."""
    track = create_mock_track(
        artist="Artist",
        album="Album",
        title="Title",
        track_number=5,
        disc_number=1,
        genre="Rock",
        year=2023,
        comment="Comment",
        composer="Composer",
        grouping="Grouping",
        bpm=120,
        file_path=Path("/music/song.mp3"),
    )

    pattern = "%artist% - %album% - %title%"
    result = generate_filename(track, pattern)
    assert result == "Artist - Album - Title"


def test_generate_filename_track_padding():
    """Test track number padding."""
    track = create_mock_track(track_number=5, file_path=Path("song.mp3"))

    pattern = "%track%"
    result = generate_filename(track, pattern)
    assert result == "5"  # No padding

    pattern = "%track2%"
    result = generate_filename(track, pattern)
    assert result == "05"  # 2-digit padding

    pattern = "%track3%"
    result = generate_filename(track, pattern)
    assert result == "005"  # 3-digit padding


def test_generate_filename_filename_and_ext():
    """Test filename and extension placeholders."""
    track = create_mock_track(file_path=Path("/path/to/song.mp3"))

    pattern = "%filename%"
    result = generate_filename(track, pattern)
    assert result == "song"

    pattern = "%ext%"
    result = generate_filename(track, pattern)
    assert result == "mp3"


def test_generate_filename_empty_values():
    """Test with empty tag values."""
    track = create_mock_track(file_path=Path("song.mp3"))

    pattern = "%artist% - %title%"
    result = generate_filename(track, pattern)
    # sanitize_filename strips trailing spaces, so " - " becomes " -"
    assert result.startswith(" -")


def test_rename_track_success(temp_dir):
    """Test successful track rename."""
    # Create source file
    src = Path(temp_dir) / "source.mp3"
    src.write_text("audio content")

    track = create_mock_track(file_path=src, artist="Artist", title="Title")

    pattern = "%artist% - %title%.mp3"

    with patch("metatag.utils.rename_utils.file_utils.safe_move") as mock_move:
        mock_move.return_value = True
        result = rename_track(track, pattern, base_dir=temp_dir)

        assert result is True
        mock_move.assert_called_once()

        # Check destination path
        call_args = mock_move.call_args[0]
        assert call_args[0] == str(src)
        assert call_args[1].endswith("Artist - Title.mp3")

        # Check track's file_path was updated via update_path()
        track.update_path.assert_called_once()

def test_rename_track_same_destination(temp_dir):
    """Test rename when destination is same as source."""
    src = Path(temp_dir) / "song.mp3"
    src.write_text("content")

    track = create_mock_track(file_path=src)

    # Pattern that results in same filename
    pattern = "%filename%.mp3"

    result = rename_track(track, pattern, base_dir=temp_dir)
    assert result is True  # Should return True without moving


def test_rename_track_move_fails(temp_dir):
    """Test rename when safe_move fails."""
    src = Path(temp_dir) / "source.mp3"
    src.write_text("content")

    track = create_mock_track(file_path=src, artist="Artist")

    pattern = "%artist%.mp3"

    with patch("metatag.utils.rename_utils.file_utils.safe_move") as mock_move:
        mock_move.return_value = False
        result = rename_track(track, pattern, base_dir=temp_dir)

        assert result is False
        mock_move.assert_called_once()


def test_rename_track_no_base_dir(temp_dir):
    """Test rename using track's directory as base."""
    src = Path(temp_dir) / "subdir" / "song.mp3"
    src.parent.mkdir(parents=True)
    src.write_text("content")

    track = create_mock_track(file_path=src, artist="Artist")

    pattern = "%artist%.mp3"

    with patch("metatag.utils.rename_utils.file_utils.safe_move") as mock_move:
        mock_move.return_value = True
        result = rename_track(track, pattern, base_dir=None)

        assert result is True
        # Should use track's parent directory
        call_args = mock_move.call_args[0]
        assert str(Path(call_args[1]).parent) == str(src.parent)


def test_rename_tracks_multiple():
    """Test renaming multiple tracks."""
    tracks = []
    for i in range(3):
        track = create_mock_track(file_path=Path(f"song{i}.mp3"), artist=f"Artist{i}")
        tracks.append(track)

    pattern = "%artist%.mp3"

    with patch("metatag.utils.rename_utils.rename_track") as mock_rename:
        mock_rename.side_effect = [True, False, True]
        results = rename_tracks(tracks, pattern)

        assert mock_rename.call_count == 3
        assert results == {0: True, 1: False, 2: True}


if __name__ == "__main__":
    pytest.main([__file__])
