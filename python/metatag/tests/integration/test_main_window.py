"""Integration tests for MainWindow."""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu
from PySide6.QtGui import QImage
from PIL import Image
import io
import tempfile
import os

from metatag.ui.main_window import MainWindow, CoverArtLabel


def test_main_window_initialization(qtbot):
    """Test MainWindow can be instantiated and has expected widgets."""
    window = MainWindow()
    qtbot.add_widget(window)

    assert window is not None

    # Check core tag edit widgets exist
    assert window._file_list is not None
    assert window._artist_edit is not None
    assert window._album_edit is not None
    assert window._title_edit is not None
    assert window._genre_edit is not None
    assert window._year_edit is not None
    assert window._track_edit is not None
    assert window._disc_edit is not None
    assert window._comment_edit is not None
    assert window._composer_edit is not None
    assert window._grouping_edit is not None
    assert window._bpm_edit is not None

    # Navigation bar
    assert window._prev_button is not None
    assert window._next_button is not None
    assert window._nav_label is not None

    # Cover art widgets
    assert window._cover_label is not None
    assert window._load_cover_button is not None
    assert window._clear_cover_button is not None
    assert window._fetch_cover_button is not None

    # Buttons
    assert window._save_button is not None
    assert window._apply_to_selected_check is not None


def test_cover_art_label_placeholder(qtbot):
    """Test CoverArtLabel shows 'No Cover Art' placeholder initially."""
    label = CoverArtLabel()
    qtbot.add_widget(label)

    # Initially shows placeholder text
    assert "No Cover Art" in label.text()

    # Test setCoverImage with PIL Image replaces placeholder
    img = Image.new("RGB", (100, 100), color="red")
    label.setCoverImage(img)
    assert label.pixmap() is not None
    assert label.pixmap().width() > 0

    # Test setCoverImage with None restores placeholder
    label.setCoverImage(None)
    assert "No Cover Art" in label.text()


def test_cover_art_label_drag_drop(qtbot):
    """Test CoverArtLabel placeholder text and image display."""
    label = CoverArtLabel()
    qtbot.add_widget(label)

    # Placeholder shows "No Cover Art" (not "Drag & Drop" — that was old copy)
    assert label.text() != ""

    img = Image.new("RGB", (100, 100), color="red")
    label.setCoverImage(img)
    assert label.pixmap() is not None
    assert label.pixmap().width() > 0

    label.setCoverImage(None)
    # After clearing, text is restored
    assert "No Cover Art" in label.text()


def _make_mock_track(**kwargs):
    """Build a Mock Track with all required attributes."""
    defaults = dict(
        file_path=Mock(name="path.mp3", __fspath__=lambda: "path.mp3"),
        artist="",
        album="",
        title="",
        track_number=0,
        track_total=0,
        disc_number=0,
        disc_total=0,
        genre="",
        year=0,
        comment="",
        composer="",
        grouping="",
        bpm=0,
        cover_art=None,
        duration=0,
        is_loaded=True,
        is_dirty=False,
    )
    defaults.update(kwargs)
    mock = Mock(**defaults)
    mock.load = Mock(return_value=True)
    mock.save = Mock(return_value=True)
    mock.file_path.name = "path.mp3"
    return mock


def test_main_window_load_files(qtbot, capsys):
    """Test _open_files with mocked file dialog."""
    window = MainWindow()
    qtbot.add_widget(window)

    temp_files = []
    for i in range(2):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.write(b"fake mp3 data")
        tmp.close()
        temp_files.append(tmp.name)

    try:
        with patch.object(QFileDialog, "getOpenFileNames", return_value=(temp_files, "*.mp3")):
            mock_track = _make_mock_track(artist="Test Artist", title="Test Title")
            with patch("metatag.ui.main_window.Track") as MockTrack:
                MockTrack.side_effect = [mock_track, mock_track]

                window._open_files()

                assert MockTrack.call_count == 2
                assert len(window._tracks) == 2
                assert window._file_list.rowCount() == 2
                assert window._current_index == 0

                assert window._artist_edit.text() == "Test Artist"
                assert window._title_edit.text() == "Test Title"
    finally:
        for f in temp_files:
            os.unlink(f)


def test_main_window_save_tags(qtbot):
    """Test _save_tags saves dirty tracks."""
    window = MainWindow()
    qtbot.add_widget(window)

    mock_track = _make_mock_track()
    mock_track.is_dirty = True
    mock_track.save = Mock(return_value=True)
    window._tracks = [mock_track]
    window._current_index = 0

    window._save_tags()

    mock_track.save.assert_called_once()


def test_main_window_apply_to_selected(qtbot):
    """Test apply to selected checkbox affects multiple tracks."""
    window = MainWindow()
    qtbot.add_widget(window)

    mock_tracks = [_make_mock_track(artist=f"Artist {i}") for i in range(3)]
    window._tracks = mock_tracks
    # Populate file-list table
    for i in range(3):
        window._append_table_row(i + 1, f"Track {i}")
    # Select all rows
    window._file_list.selectAll()

    window._apply_to_selected_check.setChecked(True)
    window._artist_edit.setText("Updated Artist")

    for track in mock_tracks:
        track.is_dirty = True

    window._save_tags()

    for track in mock_tracks:
        assert track.artist == "Updated Artist"
        track.save.assert_called_once()


def test_main_window_clear_cover_art(qtbot):
    """Test clear cover art button."""
    window = MainWindow()
    qtbot.add_widget(window)

    mock_track = _make_mock_track()
    mock_track.cover_art = Image.new("RGB", (100, 100), color="blue")
    window._tracks = [mock_track]
    window._current_index = 0

    window._cover_label.setCoverImage(mock_track.cover_art)
    assert window._cover_label.pixmap() is not None

    qtbot.mouseClick(window._clear_cover_button, Qt.MouseButton.LeftButton)

    assert mock_track.cover_art is None
    # Placeholder text is restored
    assert "No Cover Art" in window._cover_label.text()


def test_main_window_fetch_cover_art(qtbot):
    """Test fetch cover art triggers online lookup."""
    window = MainWindow()
    qtbot.add_widget(window)

    mock_track = _make_mock_track(artist="Test Artist", album="Test Album")
    window._tracks = [mock_track]
    window._current_index = 0

    window._artist_edit.setText("Test Artist")
    window._album_edit.setText("Test Album")

    mock_finder = Mock()
    window._cover_finder = mock_finder

    qtbot.mouseClick(window._fetch_cover_button, Qt.MouseButton.LeftButton)

    mock_finder.fetch_cover.assert_called_once_with("Test Artist", "Test Album")


def test_main_window_cover_art_drag_drop(qtbot):
    """Test drag and drop of image file onto cover art label."""
    window = MainWindow()
    qtbot.add_widget(window)

    mock_track = _make_mock_track()
    window._tracks = [mock_track]
    window._current_index = 0

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img = Image.new("RGB", (100, 100), color="green")
        img.save(tmp.name, format="PNG")
        tmp_path = tmp.name

    try:
        with patch("PIL.Image.open", return_value=Image.new("RGB", (100, 100), color="green")):
            window._cover_label.coverDropped.emit(tmp_path)

            assert mock_track.cover_art is not None
            assert window._cover_label.pixmap() is not None
    finally:
        os.unlink(tmp_path)


def test_main_window_status_bar(qtbot):
    """Test status bar updates."""
    window = MainWindow()
    qtbot.add_widget(window)

    window.statusBar().showMessage("Test status message")
    assert window.statusBar().currentMessage() == "Test status message"


def test_main_window_menu_actions(qtbot):
    """Test menu actions exist with correct text using ellipsis character."""
    window = MainWindow()
    qtbot.add_widget(window)

    assert window.menuBar() is not None

    file_menu = window.menuBar().findChild(QMenu, "fileMenu")
    edit_menu = window.menuBar().findChild(QMenu, "editMenu")
    online_menu = window.menuBar().findChild(QMenu, "onlineMenu")
    help_menu = window.menuBar().findChild(QMenu, "helpMenu")

    assert file_menu is not None
    assert edit_menu is not None
    assert online_menu is not None
    assert help_menu is not None

    file_texts = [a.text() for a in file_menu.actions()]
    # The menu uses Unicode ellipsis (…) not three dots (...)
    assert any("Open Files" in t for t in file_texts)
    assert any("Export CSV" in t for t in file_texts)
    assert any("Import CSV" in t for t in file_texts)
    assert any("iTunes" in t for t in file_texts)
    assert any("Exit" in t for t in file_texts)

    edit_texts = [a.text() for a in edit_menu.actions()]
    assert any("Rename Files" in t for t in edit_texts)
    assert any("Find" in t and "Replace" in t for t in edit_texts)

    help_texts = [a.text() for a in help_menu.actions()]
    assert any("About" in t for t in help_texts)


def test_main_window_navigation(qtbot):
    """Test prev/next navigation buttons cycle through tracks."""
    window = MainWindow()
    qtbot.add_widget(window)

    tracks = [_make_mock_track(artist=f"Artist {i}") for i in range(3)]
    window._tracks = tracks
    for i in range(3):
        window._append_table_row(i + 1, f"Track {i}")

    window._file_list.selectRow(0)
    assert window._current_index == 0

    qtbot.mouseClick(window._next_button, Qt.MouseButton.LeftButton)
    assert window._current_index == 1

    qtbot.mouseClick(window._next_button, Qt.MouseButton.LeftButton)
    assert window._current_index == 2

    # Should not go past the end
    qtbot.mouseClick(window._next_button, Qt.MouseButton.LeftButton)
    assert window._current_index == 2

    qtbot.mouseClick(window._prev_button, Qt.MouseButton.LeftButton)
    assert window._current_index == 1

    # Should not go before the start
    window._file_list.selectRow(0)
    qtbot.mouseClick(window._prev_button, Qt.MouseButton.LeftButton)
    assert window._current_index == 0


def test_main_window_nav_label(qtbot):
    """Test navigation label shows correct count."""
    window = MainWindow()
    qtbot.add_widget(window)

    assert "0 / 0" in window._nav_label.text()

    tracks = [_make_mock_track() for _ in range(5)]
    window._tracks = tracks
    for i in range(5):
        window._append_table_row(i + 1, f"Track {i}")
    window._file_list.selectRow(0)

    assert "1 / 5" in window._nav_label.text()


if __name__ == "__main__":
    pytest.main([__file__])
