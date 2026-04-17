"""Unit tests for Track class."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from PIL import Image
import io

from metatag.core.track import Track


def test_track_initialization():
    """Test Track constructor sets default values."""
    track = Track("/some/path.mp3")
    assert track.file_path == Path("/some/path.mp3")
    assert track.artist == ""
    assert track.album == ""
    assert track.title == ""
    assert track.track_number == 0
    assert track.disc_number == 0
    assert track.genre == ""
    assert track.year == 0
    assert track.comment == ""
    assert track.composer == ""
    assert track.grouping == ""
    assert track.bpm == 0
    assert track.cover_art is None
    assert track.duration == 0
    assert not track.is_loaded
    assert not track.is_dirty


def test_track_setters_mark_dirty():
    """Test that setting properties marks track as dirty."""
    track = Track("/some/path.mp3")
    assert not track.is_dirty

    track.artist = "New Artist"
    assert track.artist == "New Artist"
    assert track.is_dirty

    track._dirty = False
    track.album = "New Album"
    assert track.is_dirty

    track._dirty = False
    track.title = "New Title"
    assert track.is_dirty

    track._dirty = False
    track.track_number = 5
    assert track.is_dirty

    track._dirty = False
    track.disc_number = 2
    assert track.is_dirty

    track._dirty = False
    track.genre = "Rock"
    assert track.is_dirty

    track._dirty = False
    track.year = 2023
    assert track.is_dirty

    track._dirty = False
    track.comment = "Test comment"
    assert track.is_dirty

    track._dirty = False
    track.composer = "Composer"
    assert track.is_dirty

    track._dirty = False
    track.grouping = "Group"
    assert track.is_dirty

    track._dirty = False
    track.bpm = 120
    assert track.is_dirty

    track._dirty = False
    track.cover_art = Image.new("RGB", (100, 100))
    assert track.is_dirty


def test_track_setters_same_value_no_dirty():
    """Test that setting property to same value does not mark dirty."""
    track = Track("/some/path.mp3")
    track._artist = "Artist"
    track._dirty = False
    track.artist = "Artist"  # same value
    assert not track.is_dirty


def test_load_success_mock(mocker):
    """Test load() with mocked mutagen."""
    mock_mutagen_file = Mock()
    mock_mutagen_file.info = Mock(length=180.5)  # 180.5 seconds
    mock_easy = Mock()
    mock_easy.get.side_effect = lambda key, default: {
        "artist": ["Test Artist"],
        "album": ["Test Album"],
        "title": ["Test Title"],
        "tracknumber": ["5/10"],
        "genre": ["Rock"],
        "date": ["2023"],
        "comment": ["Test comment"],
    }.get(key, default)

    mocker.patch("mutagen.File", side_effect=[mock_mutagen_file, mock_easy])

    track = Track("/some/path.mp3")
    result = track.load()

    assert result is True
    assert track.is_loaded is True
    assert track.is_dirty is False
    assert track.artist == "Test Artist"
    assert track.album == "Test Album"
    assert track.title == "Test Title"
    assert track.track_number == 5
    assert track.genre == "Rock"
    assert track.year == 2023
    assert track.comment == "Test comment"
    assert track.duration == 180500  # ms


def test_load_unsupported_format(mocker):
    """Test load() when mutagen returns None."""
    mocker.patch("mutagen.File", return_value=None)
    track = Track("/some/path.mp3")
    result = track.load()
    assert result is False
    assert not track.is_loaded


def test_load_exception(mocker):
    """Test load() when mutagen raises exception."""
    mocker.patch("mutagen.File", side_effect=Exception("Test error"))
    track = Track("/some/path.mp3")
    result = track.load()
    assert result is False
    assert not track.is_loaded


def test_save_no_changes():
    """Test save() returns True immediately when track is not dirty."""
    track = Track("/some/path.mp3")
    # _dirty is False by default — should short-circuit
    result = track.save()
    assert result is True


def test_save_with_changes_mock(mocker):
    """Test save() writes all fields through a single non-easy mutagen handle."""
    from mutagen.id3 import ID3

    # Build a mock mutagen file whose .tags is a real-looking ID3-like object
    mock_id3 = Mock(spec=ID3)
    added_frames = {}

    def _add(frame):
        added_frames[type(frame).__name__] = frame

    def _delall(prefix):
        pass

    mock_id3.add.side_effect = _add
    mock_id3.delall.side_effect = _delall
    mock_id3.__contains__ = Mock(return_value=False)

    mock_mutagen_file = Mock()
    mock_mutagen_file.tags = mock_id3

    mocker.patch("mutagen.File", return_value=mock_mutagen_file)

    track = Track("/some/path.mp3")
    track._loaded = True
    track._dirty = True
    track._artist = "Saved Artist"
    track._album = "Saved Album"
    track._title = "Saved Title"
    track._track_number = 3
    track._genre = "Pop"
    track._year = 2024
    track._comment = "Saved comment"

    result = track.save()

    assert result is True
    assert not track.is_dirty
    # Verify frames were added
    assert "TPE1" in added_frames
    assert added_frames["TPE1"].text[0] == "Saved Artist"
    assert "TALB" in added_frames
    assert added_frames["TALB"].text[0] == "Saved Album"
    assert "TIT2" in added_frames
    assert added_frames["TIT2"].text[0] == "Saved Title"
    assert "TRCK" in added_frames
    assert "Saved Artist" in added_frames["TPE1"].text


def test_save_exception(mocker):
    """Test save() when mutagen raises exception."""
    mocker.patch("mutagen.File", side_effect=Exception("Save error"))
    track = Track("/some/path.mp3")
    track._loaded = True
    track._dirty = True
    result = track.save()
    assert result is False


def test_cover_art_setter():
    """Test cover_art property setter."""
    track = Track("/some/path.mp3")
    img = Image.new("RGB", (200, 200), color="red")
    track.cover_art = img
    assert track.cover_art == img
    assert track.is_dirty


def test_cover_art_setter_none():
    """Test setting cover_art to None."""
    track = Track("/some/path.mp3")
    track._cover_art = Image.new("RGB", (10, 10))
    track._dirty = False
    track.cover_art = None
    assert track.cover_art is None
    assert track.is_dirty


def test_duration_property_readonly():
    """Test duration property is read-only."""
    track = Track("/some/path.mp3")
    track._duration = 5000
    assert track.duration == 5000
    # Should not be able to set
    with pytest.raises(AttributeError):
        track.duration = 6000


if __name__ == "__main__":
    pytest.main([__file__])
