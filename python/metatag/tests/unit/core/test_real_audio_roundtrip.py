"""Real audio round-trip tests using disposable ffmpeg-generated audio fixtures.

Tests load, tag editing, saving, and reloading across real audio containers:
MP3, FLAC, Ogg Vorbis, M4A, and WAV.
"""

import shutil
import subprocess
import pytest
from pathlib import Path
from PIL import Image

from metatag.core.track import Track

if not shutil.which("ffmpeg"):
    pytest.skip("ffmpeg executable not found in PATH", allow_module_level=True)


def _make_audio(path: Path, codec: str) -> None:
    """Generate a valid, minimal 0.1s silent audio file using ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=0.1",
        "-c:a", codec, str(path)
    ]
    subprocess.run(cmd, check=True)


@pytest.fixture
def make_audio_file(tmp_path):
    """Fixture providing a helper function to create real audio files."""
    codecs = {
        ".mp3": "libmp3lame",
        ".flac": "flac",
        ".ogg": "libvorbis",
        ".m4a": "aac",
        ".wav": "pcm_s16le",
    }
    def _create(ext: str) -> Path:
        codec = codecs.get(ext)
        if not codec:
            raise ValueError(f"Unsupported extension {ext}")
        file_path = tmp_path / f"test{ext}"
        _make_audio(file_path, codec)
        return file_path

    return _create


@pytest.mark.parametrize("ext", [".mp3", ".flac", ".ogg", ".m4a", ".wav"])
def test_real_audio_tag_roundtrip(make_audio_file, ext):
    """Test setting, saving, and reloading basic metadata on real audio files."""
    file_path = make_audio_file(ext)

    track = Track(file_path)
    assert track.load() is True

    track.artist = "Roundtrip Artist"
    track.album = "Roundtrip Album"
    track.title = "Roundtrip Title"
    track.genre = "Test Genre"
    track.year = 2024
    track.track_number = 3
    track.track_total = 10
    track.comment = "Roundtrip Comment"

    assert track.is_dirty is True
    assert track.save() is True
    assert track.is_dirty is False

    # Reload into a fresh Track instance
    reloaded = Track(file_path)
    assert reloaded.load() is True

    assert reloaded.artist == "Roundtrip Artist"
    assert reloaded.album == "Roundtrip Album"
    assert reloaded.title == "Roundtrip Title"
    assert reloaded.genre == "Test Genre"
    assert reloaded.year == 2024
    assert reloaded.track_number == 3
    if ext != ".wav":  # WAV standard RIFF tags don't support track total
        assert reloaded.track_total == 10
    assert reloaded.comment == "Roundtrip Comment"


@pytest.mark.parametrize("ext", [".mp3", ".flac", ".ogg", ".m4a"])
def test_real_audio_cover_art_roundtrip(make_audio_file, ext):
    """Test embedding cover art, saving, reloading, and clearing."""
    file_path = make_audio_file(ext)

    track = Track(file_path)
    assert track.load() is True
    assert track.cover_art is None

    # Embed a 64x64 solid color image
    img = Image.new("RGB", (64, 64), color="red")
    track.cover_art = img
    assert track.save() is True

    # Reload and verify image is present
    reloaded = Track(file_path)
    assert reloaded.load() is True
    assert reloaded.cover_art is not None
    assert reloaded.cover_art.size == (64, 64)

    # Now test explicit cover removal (Finding #22 / #3)
    reloaded.cover_art = None
    assert reloaded.is_dirty is True
    assert reloaded.save() is True

    reloaded_cleared = Track(file_path)
    assert reloaded_cleared.load() is True
    assert reloaded_cleared.cover_art is None


def test_real_audio_unrelated_edit_preserves_untouched_metadata(make_audio_file):
    """Test that modifying only genre preserves untouched fields and cover art (Finding #2)."""
    file_path = make_audio_file(".flac")

    # Initial full save
    track = Track(file_path)
    assert track.load() is True
    track.artist = "Preserved Artist"
    track.album = "Preserved Album"
    track.title = "Preserved Title"
    track.year = 2022
    track.comment = "Preserved Comment"
    img = Image.new("RGB", (32, 32), color="blue")
    track.cover_art = img
    assert track.save() is True

    # Now reload, change ONLY genre, and save
    edit_track = Track(file_path)
    assert edit_track.load() is True
    edit_track.genre = "New Genre"
    assert edit_track.save() is True

    # Reload again into fresh instance to verify preservation
    final_track = Track(file_path)
    assert final_track.load() is True
    assert final_track.genre == "New Genre"
    assert final_track.artist == "Preserved Artist"
    assert final_track.album == "Preserved Album"
    assert final_track.title == "Preserved Title"
    assert final_track.year == 2022
    assert final_track.comment == "Preserved Comment"
    assert final_track.cover_art is not None
    assert final_track.cover_art.size == (32, 32)
