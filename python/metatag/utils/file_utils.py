"""File utilities."""

import os
import shutil
from pathlib import Path
from typing import List


import tempfile


def safe_move(src: str, dst: str) -> bool:
    """Move file safely, creating destination directory if needed."""
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            return False

        if dst_path.exists():
            try:
                if src_path.samefile(dst_path):
                    return True
            except OSError:
                if src_path.resolve() == dst_path.resolve():
                    return True

        dst_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            os.replace(src_path, dst_path)
            return True
        except OSError:
            # Cross-filesystem or fallback: stage via temp file in dst.parent
            tmp_fd, tmp_name = tempfile.mkstemp(
                dir=str(dst_path.parent),
                prefix=f".{dst_path.name}.tmp",
            )
            os.close(tmp_fd)
            tmp_path = Path(tmp_name)
            try:
                shutil.copy2(str(src_path), str(tmp_path))
                os.replace(tmp_path, dst_path)
                src_path.unlink()
                return True
            except Exception:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except OSError:
                        pass
                return False
    except Exception:
        return False


def safe_copy(src: str, dst: str) -> bool:
    """Copy file safely, staging replacement to protect existing destination."""
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            return False

        if dst_path.exists():
            try:
                if src_path.samefile(dst_path):
                    return True
            except OSError:
                if src_path.resolve() == dst_path.resolve():
                    return True

        dst_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_fd, tmp_name = tempfile.mkstemp(
            dir=str(dst_path.parent),
            prefix=f".{dst_path.name}.tmp",
        )
        os.close(tmp_fd)
        tmp_path = Path(tmp_name)
        try:
            shutil.copy2(str(src_path), str(tmp_path))
            os.replace(tmp_path, dst_path)
            return True
        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            return False
    except Exception:
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
        ".m4b", ".m4p",  # FIX #10: audiobook formats missing from folder scan
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
