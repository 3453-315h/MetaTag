"""
Pytest fixtures for MetaTag tests.
"""

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
import sys
import os
import tempfile
import shutil


@pytest.fixture(scope="session")
def qapp():
    """
    Provide a QApplication instance for the test session.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No cleanup needed, QApplication persists


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.
    """
    tmpdir = tempfile.mkdtemp(prefix="metatag_test_")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def close_message_boxes(qapp):
    """Auto‑close any QMessageBox that appears during a test."""

    def closer():
        # Find any active modal widget (should be a QMessageBox)
        active = qapp.activeModalWidget()
        if isinstance(active, QMessageBox):
            # Accept the message box (closes it)
            active.accept()

    return closer


@pytest.fixture
def sample_audio_path(temp_dir):
    """
    Create a minimal but **valid** FLAC file for testing.

    The file is 42 bytes: fLaC magic + a single STREAMINFO metadata block
    (the only mandatory FLAC block).  Mutagen can open and read/write tags on
    this file without audio frame data.
    """
    import struct

    path = os.path.join(temp_dir, "sample.flac")

    # STREAMINFO content (34 bytes)
    # See https://xiph.org/flac/format.html#metadata_block_streaminfo
    min_block = max_block = 4096
    min_frame = max_frame = 0
    sample_rate = 44100   # Hz
    channels = 2          # stereo
    bps = 16              # bits per sample
    total_samples = 0

    # Pack the 64-bit sample-info field:
    # [20b sample_rate | 3b (channels-1) | 5b (bps-1) | 36b total_samples]
    sample_info = struct.pack(
        ">Q",
        (sample_rate << 44) | ((channels - 1) << 41) | ((bps - 1) << 36) | total_samples,
    )

    streaminfo = (
        struct.pack(">HH", min_block, max_block)   # 4 bytes
        + struct.pack(">I", min_frame)[1:]          # 3 bytes
        + struct.pack(">I", max_frame)[1:]          # 3 bytes
        + sample_info                               # 8 bytes
        + b"\x00" * 16                              # MD5 (16 bytes)
    )  # total 34 bytes

    # Block header: last=1, type=0 (STREAMINFO), length=34
    block_header = struct.pack(">I", (1 << 31) | (0 << 24) | len(streaminfo))

    with open(path, "wb") as f:
        f.write(b"fLaC")
        f.write(block_header)
        f.write(streaminfo)

    return path


@pytest.fixture
def usable_flac_path(sample_audio_path):
    """
    Like sample_audio_path but pre-tagged with test metadata via mutagen,
    for tests that need a full load/save round-trip.
    """
    from mutagen.flac import FLAC

    flac = FLAC(sample_audio_path)
    flac["title"] = ["Test Track"]
    flac["artist"] = ["Test Artist"]
    flac["album"] = ["Test Album"]
    flac["tracknumber"] = ["1/10"]
    flac["date"] = ["2024"]
    flac["genre"] = ["Electronic"]
    flac.save()
    return sample_audio_path

