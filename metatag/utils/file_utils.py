"""File utilities."""

import os
import shutil
from pathlib import Path
from typing import List


def safe_move(src: str, dst: str) -> bool:
    """Move file safely, creating destination directory if needed."""
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        return False

    # Ensure destination directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove destination if exists
    if dst_path.exists():
        try:
            dst_path.unlink()
        except OSError:
            return False

    try:
        shutil.move(str(src_path), str(dst_path))
        return True
    except (OSError, shutil.Error):
        return False


def safe_copy(src: str, dst: str) -> bool:
    """Copy file safely."""
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        return False

    dst_path.parent.mkdir(parents=True, exist_ok=True)

    if dst_path.exists():
        try:
            dst_path.unlink()
        except OSError:
            return False

    try:
        shutil.copy2(str(src_path), str(dst_path))
        return True
    except (OSError, shutil.Error):
        return False


def safe_delete(path: str) -> bool:
    """Delete file if it exists."""
    path_obj = Path(path)
    if not path_obj.exists():
        return True
    try:
        path_obj.unlink()
        return True
    except OSError:
        return False


def find_audio_files(directory: str, recursive: bool = True) -> List[str]:
    """Find audio files in directory, optionally recursive."""
    audio_extensions = {
        ".mp3", ".flac", ".wav", ".aiff", ".ogg", ".m4a", ".mp4",
        ".oga", ".spx", ".opus", ".wma", ".aac",
    }

    result = []
    dir_path = Path(directory)
    if not dir_path.exists():
        return result

    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in audio_extensions:
                    result.append(str(Path(root) / file))
    else:
        for file in os.listdir(directory):
            file_path = dir_path / file
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                result.append(str(file_path))

    return result
