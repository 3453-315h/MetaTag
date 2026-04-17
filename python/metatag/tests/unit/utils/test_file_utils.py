"""Unit tests for file_utils."""

import os
import pytest
from pathlib import Path
from metatag.utils.file_utils import (
    safe_move,
    safe_copy,
    safe_delete,
    find_audio_files,
)


def test_safe_move_success(temp_dir):
    """Test successful file move."""
    src = Path(temp_dir) / "source.txt"
    dst = Path(temp_dir) / "dest.txt"

    # Create source file
    src.write_text("test content")
    assert src.exists()

    result = safe_move(str(src), str(dst))
    assert result is True
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == "test content"


def test_safe_move_source_not_exists(temp_dir):
    """Test move when source doesn't exist."""
    src = Path(temp_dir) / "nonexistent.txt"
    dst = Path(temp_dir) / "dest.txt"

    result = safe_move(str(src), str(dst))
    assert result is False
    assert not dst.exists()


def test_safe_move_destination_exists(temp_dir):
    """Test move when destination exists (should overwrite)."""
    src = Path(temp_dir) / "source.txt"
    dst = Path(temp_dir) / "dest.txt"

    src.write_text("new content")
    dst.write_text("old content")

    result = safe_move(str(src), str(dst))
    assert result is True
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == "new content"


def test_safe_move_create_directories(temp_dir):
    """Test move creating destination directories."""
    src = Path(temp_dir) / "source.txt"
    dst = Path(temp_dir) / "subdir" / "nested" / "dest.txt"

    src.write_text("test")

    result = safe_move(str(src), str(dst))
    assert result is True
    assert dst.parent.exists()
    assert dst.exists()


def test_safe_copy_success(temp_dir):
    """Test successful file copy."""
    src = Path(temp_dir) / "source.txt"
    dst = Path(temp_dir) / "dest.txt"

    src.write_text("test content")

    result = safe_copy(str(src), str(dst))
    assert result is True
    assert src.exists()  # Source should still exist
    assert dst.exists()
    assert dst.read_text() == "test content"


def test_safe_copy_source_not_exists(temp_dir):
    """Test copy when source doesn't exist."""
    src = Path(temp_dir) / "nonexistent.txt"
    dst = Path(temp_dir) / "dest.txt"

    result = safe_copy(str(src), str(dst))
    assert result is False


def test_safe_copy_destination_exists(temp_dir):
    """Test copy when destination exists (should overwrite)."""
    src = Path(temp_dir) / "source.txt"
    dst = Path(temp_dir) / "dest.txt"

    src.write_text("new content")
    dst.write_text("old content")

    result = safe_copy(str(src), str(dst))
    assert result is True
    assert dst.read_text() == "new content"


def test_safe_delete_success(temp_dir):
    """Test successful file deletion."""
    file_path = Path(temp_dir) / "test.txt"
    file_path.write_text("content")

    result = safe_delete(str(file_path))
    assert result is True
    assert not file_path.exists()


def test_safe_delete_not_exists(temp_dir):
    """Test delete when file doesn't exist."""
    file_path = Path(temp_dir) / "nonexistent.txt"

    result = safe_delete(str(file_path))
    assert result is True  # Should return True for non-existent


def test_safe_delete_permission_error(mocker, temp_dir):
    """Test delete when permission denied (simulated)."""
    file_path = Path(temp_dir) / "test.txt"
    file_path.write_text("content")

    # Mock Path.unlink to raise OSError
    mocker.patch.object(Path, "unlink", side_effect=OSError("Permission denied"))

    result = safe_delete(str(file_path))
    assert result is False


def test_find_audio_files_basic(temp_dir):
    """Test finding audio files."""
    # Create test files
    (Path(temp_dir) / "song.mp3").write_text("")
    (Path(temp_dir) / "song.flac").write_text("")
    (Path(temp_dir) / "song.wav").write_text("")
    (Path(temp_dir) / "not_audio.txt").write_text("")
    (Path(temp_dir) / "subdir" / "song.ogg").parent.mkdir()
    (Path(temp_dir) / "subdir" / "song.ogg").write_text("")

    result = find_audio_files(temp_dir)
    result = [Path(p).name for p in result]  # Get just filenames for easier comparison

    # Should find all audio files (including in subdir)
    expected = {"song.mp3", "song.flac", "song.wav", "song.ogg"}
    assert set(result) == expected


def test_find_audio_files_case_insensitive(temp_dir):
    """Test finding audio files with different case extensions."""
    (Path(temp_dir) / "song.MP3").write_text("")
    (Path(temp_dir) / "song.Flac").write_text("")

    result = find_audio_files(temp_dir)
    result = [Path(p).name for p in result]

    assert "song.MP3" in result
    assert "song.Flac" in result


def test_find_audio_files_directory_not_exists():
    """Test finding audio files in non-existent directory."""
    result = find_audio_files("/nonexistent/path")
    assert result == []


def test_find_audio_files_empty_directory(temp_dir):
    """Test finding audio files in empty directory."""
    result = find_audio_files(temp_dir)
    assert result == []


if __name__ == "__main__":
    pytest.main([__file__])
