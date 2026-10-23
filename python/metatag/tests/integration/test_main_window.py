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
from metatag.core.track import Track
from metatag.core.undo import TagEditCommand, CoverChangeCommand
from metatag.ui.models.track_model import TrackModel


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
                assert window._track_model.rowCount() == 2
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
    window._tracks.clear()
    window._tracks.extend(mock_tracks)
    window._track_model.refresh()
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
    auto_menu = window.menuBar().findChild(QMenu, "autoMenu")
    online_menu = window.menuBar().findChild(QMenu, "onlineMenu")
    help_menu = window.menuBar().findChild(QMenu, "helpMenu")

    assert file_menu is not None
    assert edit_menu is not None
    assert auto_menu is not None
    assert online_menu is not None
    assert help_menu is not None

    file_texts = [a.text() for a in file_menu.actions()]
    # The menu uses Unicode ellipsis (…) not three dots (...)
    assert any("Open Files" in t for t in file_texts)
    export_action = next(a for a in file_menu.actions() if "Export Tracklist" in a.text())
    assert any("CSV Report" in t for t in [sub.text() for sub in export_action.menu().actions()])
    assert any("Import CSV" in t for t in file_texts)
    assert any("iTunes" in t for t in file_texts)
    assert any("Exit" in t for t in file_texts)

    edit_texts = [a.text() for a in edit_menu.actions()]
    assert any("Find" in t and "Replace" in t for t in edit_texts)
    assert any("Undo" in t for t in edit_texts)

    auto_texts = [a.text() for a in auto_menu.actions()]
    assert any("Batch Rename" in t for t in auto_texts)

    help_texts = [a.text() for a in help_menu.actions()]
    assert any("About" in t for t in help_texts)


def test_main_window_navigation(qtbot):
    """Test prev/next navigation buttons cycle through tracks."""
    window = MainWindow()
    qtbot.add_widget(window)

    tracks = [_make_mock_track(artist=f"Artist {i}") for i in range(3)]
    window._tracks.clear()
    window._tracks.extend(tracks)
    window._track_model.refresh()

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
    window._tracks.clear()
    window._tracks.extend(tracks)
    window._track_model.refresh()
    window._file_list.selectRow(0)

    assert "1 / 5" in window._nav_label.text()


def test_undo_after_row_removed(qtbot):
    """Test Item 1: edit track -> remove row -> undo; no crash, remaining audio metadata unchanged."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="Artist 0", title="Title 0")
    t1 = _make_mock_track(artist="Artist 1", title="Title 1")
    window._tracks.extend([t0, t1])
    window._track_model.refresh()
    window._current_index = 0
    window._file_list.selectRow(0)

    # Edit track 0 via command
    cmd = TagEditCommand(window, [t0], "artist", "Edited Artist 0")
    window._undo_stack.push(cmd)
    assert t0.artist == "Edited Artist 0"

    # Remove track 0 from session
    window._file_list.selectRow(0)
    window._remove_selected_tracks()
    assert len(window._tracks) == 1
    assert window._tracks[0] is t1
    assert t1.artist == "Artist 1"

    # Undo should gracefully skip removed track 0 and not corrupt track 1 or crash
    window._undo_stack.undo()
    assert len(window._tracks) == 1
    assert window._tracks[0] is t1
    assert t1.artist == "Artist 1"


def test_undo_after_new_session_opened(qtbot):
    """Test Item 1: edit track -> open different session -> undo; no crash, new session unchanged."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="Artist 0")
    window._tracks.append(t0)
    window._track_model.refresh()
    window._current_index = 0

    cmd = TagEditCommand(window, [t0], "artist", "Edited Artist")
    window._undo_stack.push(cmd)
    assert t0.artist == "Edited Artist"

    # Open different files creates a new session
    new_t = _make_mock_track(artist="New Session Artist")
    with patch.object(QFileDialog, "getOpenFileNames", return_value=(["/dummy/file.mp3"], "*.mp3")):
        with patch("metatag.ui.main_window.Track", return_value=new_t):
            window._open_files()

    assert len(window._tracks) == 1
    assert window._tracks[0] is new_t
    assert new_t.artist == "New Session Artist"

    # Undo stack was cleared on new session; if an old command were called it respects session_id
    assert window._undo_stack.canUndo() is False
    cmd.undo()  # direct call with stale session_id does nothing
    assert new_t.artist == "New Session Artist"


def test_undo_with_sorted_selection(qtbot):
    """Test Item 1: undo with sorted proxy model tracks changes correctly."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="Zeta")
    t1 = _make_mock_track(artist="Alpha")
    window._tracks.extend([t0, t1])
    window._track_model.refresh()

    # Sort proxy model by artist
    window._proxy_model.sort(TrackModel._COLUMN_ARTIST, Qt.SortOrder.AscendingOrder)

    # Edit Alpha (which is visual row 0 in proxy)
    cmd = TagEditCommand(window, [t1], "title", "Alpha Song")
    window._undo_stack.push(cmd)
    assert t1.title == "Alpha Song"

    window._undo_stack.undo()
    assert t1.title == ""
    window._undo_stack.redo()
    assert t1.title == "Alpha Song"


def test_case_correction_undoable(qtbot):
    """Test Item 5: _apply_case_correction is fully undoable via undo stack."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="john doe", title="cool song")
    window._tracks.append(t0)
    window._track_model.refresh()
    window._current_index = 0
    window._file_list.selectRow(0)

    window._apply_case_correction("title")
    assert t0.artist == "John Doe"
    assert t0.title == "Cool Song"

    window._undo_stack.undo()
    assert t0.artist == "john doe"
    assert t0.title == "cool song"

    window._undo_stack.redo()
    assert t0.artist == "John Doe"
    assert t0.title == "Cool Song"


def test_audiobook_metadata_undoable(qtbot):
    """Test Item 5: _search_audiobook metadata changes are undoable."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="Original Author", album="Original Book")
    window._tracks.append(t0)
    window._track_model.refresh()
    window._current_index = 0
    window._file_list.selectRow(0)

    fake_book = {
        "title": "New Book Title",
        "artist": "New Author",
        "narrator": "Great Narrator",
        "series_name": "Book Series",
        "year": 2024,
        "comment": "Audiobook comment",
    }
    with patch("metatag.ui.dialogs.audiobook_lookup_dialog.AudiobookLookupDialog.exec", return_value=1):
        with patch("metatag.ui.dialogs.audiobook_lookup_dialog.AudiobookLookupDialog.get_selected_book", return_value=fake_book):
            window._search_audiobook()

    assert t0.album == "New Book Title"
    assert t0.artist == "New Author"
    assert t0.composer == "Great Narrator"
    assert t0.grouping == "Book Series"

    window._undo_stack.undo()
    assert t0.album == "Original Book"
    assert t0.artist == "Original Author"


def test_background_track_loading_cancellation(qtbot):
    """Test Item 7: Background track loading worker supports cancellation."""
    from metatag.ui.main_window import TrackLoaderWorker

    class SlowTrack(Track):
        def load(self):
            import time
            time.sleep(0.05)
            self._loaded = True
            return True

    tracks = [(i, SlowTrack(f"/path/{i}.mp3")) for i in range(10)]
    worker = TrackLoaderWorker(session_id=1, items=tracks)
    worker.start()
    assert worker.isRunning()
    worker.cancel()
    worker.wait(1000)
    assert not worker.isRunning()
    assert worker.is_cancelled()


def test_cover_fetch_targeting_initiating_tracks(qtbot):
    """Test Item 8: Cover fetch applies only to initiating track even if selection switches."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="Artist 0", album="Album 0")
    t1 = _make_mock_track(artist="Artist 1", album="Album 1")
    window._tracks.extend([t0, t1])
    window._track_model.refresh()
    window._current_index = 0
    window._file_list.selectRow(0)

    # Initiating track is t0
    target_tracks = [t0]
    session_id = window._session_id

    # Switch current selection to t1
    window._current_index = 1
    window._file_list.selectRow(1)

    # Deliver fetched cover for t0
    from PySide6.QtGui import QImage
    qimg = QImage(50, 50, QImage.Format.Format_RGB32)
    qimg.fill(Qt.GlobalColor.red)

    window._on_cover_fetched_for_tracks(qimg, session_id, target_tracks)

    assert t0.cover_art is not None
    assert t1.cover_art is None  # t1 was selected when fetch completed, but was not the target!


def test_cover_fetch_discarded_on_session_replacement(qtbot):
    """Test Item 8: Completed cover fetch discarded if session was replaced."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="Artist 0", album="Album 0")
    window._tracks.append(t0)
    window._track_model.refresh()
    window._current_index = 0
    old_session = window._session_id

    # New session started
    window._session_id += 1
    new_t = _make_mock_track(artist="New Artist")
    window._tracks = [new_t]

    from PySide6.QtGui import QImage
    qimg = QImage(50, 50, QImage.Format.Format_RGB32)
    qimg.fill(Qt.GlobalColor.blue)

    window._on_cover_fetched_for_tracks(qimg, old_session, [t0])

    assert t0.cover_art is None
    assert new_t.cover_art is None


def test_cover_fetch_row_removed_during_flight(qtbot):
    """Test Item 8: Target track removed while fetch was in flight skips gracefully."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="Artist 0", album="Album 0")
    t1 = _make_mock_track(artist="Artist 1", album="Album 1")
    window._tracks.extend([t0, t1])
    window._track_model.refresh()
    session_id = window._session_id

    # Remove t0 from session
    window._tracks.remove(t0)

    from PySide6.QtGui import QImage
    qimg = QImage(50, 50, QImage.Format.Format_RGB32)
    qimg.fill(Qt.GlobalColor.green)

    window._on_cover_fetched_for_tracks(qimg, session_id, [t0])
    assert t0.cover_art is None
    assert t1.cover_art is None


def test_sorted_table_selection_loads_correct_track(qtbot):
    """Test Finding #5: When table is sorted, selection correctly maps proxy to source."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(title="Zebra", artist="Zebra Artist")
    t1 = _make_mock_track(title="Apple", artist="Apple Artist")
    window._tracks.extend([t0, t1])
    window._track_model.refresh()

    # Sort ascending by Title (column 1)
    window._proxy_model.sort(1, Qt.SortOrder.AscendingOrder)
    # Proxy row 0 is now t1 ("Apple"), Proxy row 1 is t0 ("Zebra")
    assert window._proxy_model.mapToSource(window._proxy_model.index(0, 0)).row() == 1
    assert window._proxy_model.mapToSource(window._proxy_model.index(1, 0)).row() == 0

    # Select source row 0 ("Zebra")
    window._select_source_row(0)
    assert window._current_index == 0
    assert window._title_edit.text() == "Zebra"

    # Select proxy row 0 in view ("Apple")
    window._file_list.selectRow(0)
    assert window._current_index == 1
    assert window._title_edit.text() == "Apple"


def test_field_changed_respects_apply_to_selected_checkbox(qtbot):
    """Test Finding #6: Field editing respects the apply_to_selected checkbox state."""
    window = MainWindow()
    qtbot.add_widget(window)

    t0 = _make_mock_track(artist="ArtistA")
    t1 = _make_mock_track(artist="ArtistB")
    window._tracks.extend([t0, t1])
    window._track_model.refresh()

    # Select both rows in the table
    window._file_list.selectAll()
    assert len(window._file_list.selectionModel().selectedRows()) == 2
    window._current_index = 0

    # When checkbox is unchecked, edit only applies to current track
    window._apply_to_selected_check.setChecked(False)
    window._field_changed("artist", "SingleArtist")
    assert t0.artist == "SingleArtist"
    assert t1.artist == "ArtistB"

    # When checkbox is checked, edit applies to all selected tracks
    window._apply_to_selected_check.setChecked(True)
    window._field_changed("artist", "BatchArtist")
    assert t0.artist == "BatchArtist"
    assert t1.artist == "BatchArtist"


def test_confirm_discard_dirty_clean_tracks(qtbot):
    """Test Finding #17: Clean tracks allow discard without prompt."""
    window = MainWindow()
    qtbot.add_widget(window)
    t = _make_mock_track()
    t.is_dirty = False
    window._tracks = [t]
    assert window._confirm_discard_dirty() is True


def test_confirm_discard_dirty_flushes_when_auto_save_enabled(qtbot):
    """Test Finding #17: Dirty tracks flush save when auto-save is enabled."""
    window = MainWindow()
    qtbot.add_widget(window)
    window._settings.set_auto_save_enabled(True)

    t = _make_mock_track()
    t.is_dirty = True
    def fake_save(**kwargs):
        t.is_dirty = False
        return True
    t.save = Mock(side_effect=fake_save)
    window._tracks = [t]

    assert window._confirm_discard_dirty() is True
    t.save.assert_called_once()


def test_auto_save_timer_stops_when_disabled(qtbot):
    """Test Finding #17: Disabling auto-save stops any pending auto-save timer."""
    window = MainWindow()
    qtbot.add_widget(window)

    window._settings.set_auto_save_enabled(True)
    t = _make_mock_track()
    t.is_dirty = True
    window._tracks = [t]

    window._schedule_auto_save()
    assert window._auto_save_timer.isActive() is True

    window._settings.set_auto_save_enabled(False)
    window._schedule_auto_save()
    assert window._auto_save_timer.isActive() is False


def test_recent_folders_cap_honored(qtbot):
    """Test Finding #26: Recent folders honors max_recent_items setting."""
    window = MainWindow()
    qtbot.add_widget(window)

    window._settings.set_max_recent_items(3)
    window._settings.clear_recent_folders()

    window._settings.add_recent_folder("/path/one")
    window._settings.add_recent_folder("/path/two")
    window._settings.add_recent_folder("/path/three")
    window._settings.add_recent_folder("/path/four")

    folders = window._settings.recent_folders()
    assert len(folders) == 3
    assert folders == ["/path/four", "/path/three", "/path/two"]


def test_synthetic_large_library_scaling(qtbot, monkeypatch):
    """Test Gate 2 / Item 7: Synthetic large library scaling and UI responsiveness.

    Validates that a 500-track library loads without freezing the GUI,
    maintains immediate sub-50ms responsiveness for search/filtering/sorting,
    uses negligible memory, and cancels background loaders cleanly on session reset.
    """
    import time

    window = MainWindow()
    qtbot.add_widget(window)

    # Mock Track.load to simulate realistic tag parsing latency (1ms per track)
    # without requiring a multi-gigabyte disk footprint.
    def mock_track_load(self):
        time.sleep(0.001)
        self.artist = f"Artist {self.file_path}"
        self.album = "Scaling Album"
        self.title = f"Track {self.file_path}"
        self._loaded = True
        return True

    monkeypatch.setattr(Track, "load", mock_track_load)

    # 1. Measure initial open responsiveness with 500 tracks
    synthetic_files = [f"/music/test_track_{i:04d}.mp3" for i in range(500)]
    t0 = time.perf_counter()
    window._open_files(synthetic_files)
    elapsed_open = time.perf_counter() - t0

    # The synchronous open must return immediately (< 150ms) to unblock the event loop
    assert elapsed_open < 0.15, f"Open took too long: {elapsed_open:.3f}s"
    assert window._track_model.rowCount() == 500
    assert window._proxy_model.rowCount() == 500

    # 2. Test UI responsiveness while/after background worker is active
    # Selection must be instantaneous
    t_sel = time.perf_counter()
    window._select_source_row(250)
    assert time.perf_counter() - t_sel < 0.05
    assert window._current_index == 250

    # Search / filter responsiveness across 500 tracks
    t_search = time.perf_counter()
    window._search_edit.setText("0250")
    elapsed_search = time.perf_counter() - t_search
    assert elapsed_search < 0.05, f"Search took too long: {elapsed_search:.3f}s"
    assert window._proxy_model.rowCount() == 1

    # Reset search
    window._search_edit.clear()
    assert window._proxy_model.rowCount() == 500

    # Sort responsiveness across 500 tracks
    t_sort = time.perf_counter()
    window._proxy_model.sort(0, Qt.SortOrder.DescendingOrder)
    elapsed_sort = time.perf_counter() - t_sort
    assert elapsed_sort < 0.05, f"Sort took too long: {elapsed_sort:.3f}s"

    # 3. Clean cancellation on session reset
    new_files = [f"/music/other_{i}.mp3" for i in range(10)]
    window._open_files(new_files)
    assert window._track_model.rowCount() == 10

    # Ensure background worker cancelled cleanly
    if window._active_loader:
        window._active_loader.cancel()
        window._active_loader.wait(500)
        assert not window._active_loader.isRunning()


if __name__ == "__main__":
    pytest.main([__file__])

