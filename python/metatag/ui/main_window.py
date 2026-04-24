"""Main window for meta — audio tag editor."""

import os
import re
import tempfile
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QFormLayout,
    QGroupBox,
    QCheckBox,
    QScrollArea,
    QSizePolicy,
    QApplication,
    QMenu,
    QSplashScreen,
    QTableView,
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPoint, QSortFilterProxyModel, QUrl, QMimeData
from PySide6.QtGui import (
    QAction,
    QPixmap,
    QIcon,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeySequence,
    QShortcut,
    QUndoStack,
    QDrag,
)
from PIL import Image
import io

PROJECT_NAME = "MetaTag"
VERSION = "1.3.1"
SUBTITLE = "Metadata Editor"

from .widgets.audio_player import AudioPlayer
from .dialogs.pattern_dialogs import TagFromFilenameDialog, BatchRenameDialog
from .dialogs.pick_release_dialog import PickReleaseDialog
from .dialogs.bulk_edit_dialog import BulkEditDialog
from ..online.musicbrainz_lookup import MusicBrainzLookup
from ..core.track import Track
from ..core.config import Settings, get_version
from ..core.undo import TagEditCommand, CoverChangeCommand
from .models.track_model import TrackModel
from ..utils.file_utils import find_audio_files
from ..utils.patterns import parse_filename, format_filename
from ..core.export import exporter
from ..utils.string_utils import to_title_case, to_upper, to_lower


def _resource_path(relative: str) -> Path:
    """Resolve asset paths for both source-run and PyInstaller bundles."""
    import sys as _sys
    try:
        base = Path(_sys._MEIPASS)  # type: ignore[attr-defined]
    except AttributeError:
        base = Path(__file__).parent.parent.parent
    return base / relative

# ─────────────────────────────────────────────────────────────────────────────
# Cover art widget
# ─────────────────────────────────────────────────────────────────────────────

class CoverArtLabel(QLabel):
    """300×300 label that displays cover art and accepts image drag-and-drop."""

    coverDropped = Signal(str)  # emits local file path
    imageDropped = Signal(object) # emits PIL.Image
    urlDropped = Signal(str) # emits web URL

    _COVER_SIZE = 300

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self._COVER_SIZE, self._COVER_SIZE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._show_placeholder()
        self.setAcceptDrops(True)
        
        # Support pasting images from clipboard
        self._paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        self._paste_shortcut.activated.connect(self._handle_paste)

        self._current_image: Optional[Image.Image] = None
        self._album_name: str = "cover"
        self._drag_start_pos: Optional[QPoint] = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._drag_start_pos is None:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
            
        self._start_drag()

    def _start_drag(self):
        if self._current_image is None:
            return
            
        # Sanitize album name for filename
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', self._album_name)
        if not safe_name:
            safe_name = "cover"
            
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{safe_name}.png")
        
        try:
            self._current_image.save(temp_path, "PNG")
        except Exception:
            return
            
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(temp_path)])
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        if self.pixmap():
            drag.setPixmap(self.pixmap().scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            drag.setHotSpot(QPoint(50, 50))
            
        drag.exec(Qt.DropAction.CopyAction)

    def _handle_paste(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime.hasImage():
            qimage = clipboard.image()
            if not qimage.isNull():
                from ..online.cover_finder import CoverFinder
                pil_image = CoverFinder().qimage_to_pil(qimage)
                self.imageDropped.emit(pil_image)

    # ---- placeholder ----

    def _show_placeholder(self) -> None:
        self.clear()
        self.setText("No Cover Art\n\n(Drag & Drop or Paste)")
        self.setStyleSheet(
            "QLabel {"
            "  border: 2px dashed #888;"
            "  border-radius: 6px;"
            "  color: #888;"
            "  font-size: 13px;"
            "}"
        )

    # ---- drag-and-drop ----

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime = event.mimeData()
        if mime.hasImage() or mime.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        mime = event.mimeData()
        
        # 1. Check for raw image data (e.g., dragged from browser)
        if mime.hasImage():
            qimage = mime.imageData()
            if qimage and not qimage.isNull():
                from ..online.cover_finder import CoverFinder
                pil_image = CoverFinder().qimage_to_pil(qimage)
                self.imageDropped.emit(pil_image)
                event.acceptProposedAction()
                return

        # 2. Check for URLs (local files or remote HTTP links)
        if mime.hasUrls():
            urls = mime.urls()
            if urls:
                url = urls[0]
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")):
                        self.coverDropped.emit(path)
                        event.acceptProposedAction()
                        return
                elif url.scheme() in ("http", "https"):
                    self.urlDropped.emit(url.toString())
                    event.acceptProposedAction()
                    return
        
        event.acceptProposedAction()

    # ---- public API ----

    def setCoverImage(self, image: Optional[Image.Image], album_name: Optional[str] = None) -> None:
        """Set cover art from a PIL Image (or None to show placeholder)."""
        self._current_image = image
        self._album_name = album_name or "cover"
        if image is None:
            self._show_placeholder()
            return
        try:
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            pixmap = QPixmap()
            if not pixmap.loadFromData(buf.getvalue()):
                raise ValueError("loadFromData failed")
            scaled = pixmap.scaled(
                self._COVER_SIZE,
                self._COVER_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
            self.setStyleSheet(
                "QLabel { border: 1px solid #555; border-radius: 4px; }"
            )
        except Exception:
            self._show_placeholder()


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Main application window."""

    _AUDIO_EXTENSIONS = (
        ".mp3", ".flac", ".wav", ".aiff", ".ogg", ".m4a", ".mp4",
        ".opus", ".wma", ".m4b", ".m4p", ".oga", ".spx",
    )

    # Table columns for the file list
    _COL_NUM   = 0
    _COL_TITLE = 1
    _COL_ARTIST = 2
    _COL_ALBUM  = 3
    _COL_DUR    = 4
    _TABLE_HEADERS = ["#", "Title", "Artist", "Album", "Duration"]

    # Field definitions: (track_attr, label text, QLineEdit attr name, placeholder)
    # track_number / disc_number use "X/Y" format strings in the UI.
    _FIELD_DEFS = [
        ("artist",       "Artist:",    "_artist_edit",   ""),
        ("album",        "Album:",     "_album_edit",    ""),
        ("title",        "Title:",     "_title_edit",    ""),
        ("track_number", "Track #:",   "_track_edit",    "e.g. 3/12"),
        ("disc_number",  "Disc #:",    "_disc_edit",     "e.g. 1/2"),
        ("year",         "Year:",      "_year_edit",     ""),
        ("genre",        "Genre:",     "_genre_edit",    ""),
        ("bpm",          "BPM:",       "_bpm_edit",      ""),
        ("composer",     "Composer:",  "_composer_edit", ""),
        ("grouping",     "Grouping:",  "_grouping_edit", ""),
        ("comment",      "Comment:",   "_comment_edit",  ""),
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._tracks: List[Track] = []
        self._current_index = -1
        self._cover_finder = None
        self._discogs_lookup = None
        self._mb_lookup = None
        self._settings = Settings()
        # Undo system
        self._undo_stack = QUndoStack(self)
        # Model/View system
        self._track_model = TrackModel(self._tracks, self)
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._track_model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(-1)  # Search all columns
        self._proxy_model.setSortRole(TrackModel.SORT_ROLE)

        # iTunes sync state
        self._last_itunes_xml: Optional[str] = None
        self._export_itunes_action: Optional[QAction] = None
        # Recent-folders menu handle (rebuilt on open)
        self._recent_menu: Optional[QMenu] = None

        # Typed field-edit attributes (set by _setup_ui; never None after that)
        self._artist_edit:   QLineEdit
        self._album_edit:    QLineEdit
        self._title_edit:    QLineEdit
        self._track_edit:    QLineEdit
        self._disc_edit:     QLineEdit
        self._year_edit:     QLineEdit
        self._genre_edit:    QLineEdit # Restored
        self._bpm_edit:      QLineEdit # Restored
        self._composer_edit: QLineEdit
        self._grouping_edit: QLineEdit
        self._comment_edit:  QLineEdit

        # Map field_key → (QLabel, QLineEdit) for data-driven operations
        self._field_widgets: dict[str, tuple[QLabel, QLineEdit]] = {}

        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.setInterval(self._settings.auto_save_interval())  # Use setting
        self._auto_save_timer.timeout.connect(self._save_tags)

        self._setup_ui()
        self._connect_signals()
        
        # Restore last directory if enabled (Disabled per user request)
        # QTimer.singleShot(0, self._restore_session)

    def _restore_session(self) -> None:
        if self._settings.restore_last_dir():
            folders = self._settings.recent_folders()
            if folders:
                self._open_recent_folder(folders[0])


    # ─────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        self.setAcceptDrops(True)

        root_layout = QVBoxLayout(central)
        root_layout.setSpacing(6)
        root_layout.setContentsMargins(8, 8, 8, 6)

        # ── Search Bar ──────────────────────────────────────────────────────────
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_edit = QLineEdit()
        self._search_edit.setObjectName("searchBar")
        self._search_edit.setPlaceholderText("Filter tracks by artist, album, title...")
        self._search_edit.setClearButtonEnabled(True)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_edit)
        root_layout.addLayout(search_layout)

        # ── File list (QTableView) ────────────────────────────────────────────
        self._file_list = QTableView()
        self._file_list.setModel(self._proxy_model)
        self._file_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._file_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._file_list.setAlternatingRowColors(True)
        self._file_list.verticalHeader().setVisible(False)
        self._file_list.setFixedHeight(180)
        self._file_list.setAcceptDrops(False)
        hh = self._file_list.horizontalHeader()
        hh.setSectionResizeMode(TrackModel._COLUMN_NUM,    QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(TrackModel._COLUMN_TITLE,  QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(TrackModel._COLUMN_ARTIST, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(TrackModel._COLUMN_ALBUM,  QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(TrackModel._COLUMN_DUR,    QHeaderView.ResizeMode.Fixed)
        self._file_list.setColumnWidth(TrackModel._COLUMN_NUM, 36)
        self._file_list.setColumnWidth(TrackModel._COLUMN_ARTIST, 150)
        self._file_list.setColumnWidth(TrackModel._COLUMN_ALBUM, 150)
        self._file_list.setColumnWidth(TrackModel._COLUMN_DUR, 60)
        self._file_list.setSortingEnabled(True)
        self._file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        root_layout.addWidget(self._file_list)

        # ── Navigation bar ────────────────────────────────────────────
        nav_layout = QHBoxLayout()
        self._prev_button = QPushButton("◀  Prev")
        self._prev_button.setFixedWidth(90)
        self._nav_label = QLabel("0 / 0")
        self._nav_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._nav_label.setMinimumWidth(100)
        self._next_button = QPushButton("Next  ▶")
        self._next_button.setFixedWidth(90)
        nav_layout.addStretch()
        nav_layout.addWidget(self._prev_button)
        nav_layout.addWidget(self._nav_label)
        nav_layout.addWidget(self._next_button)
        nav_layout.addStretch()
        root_layout.addLayout(nav_layout)

        # ── Editor area ───────────────────────────────────────────────
        editor_layout = QHBoxLayout()
        editor_layout.setSpacing(10)

        # Left: cover art
        cover_group = QGroupBox("Cover Art")
        cover_layout = QVBoxLayout(cover_group)
        cover_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._cover_label = CoverArtLabel()
        cover_layout.addWidget(
            self._cover_label, alignment=Qt.AlignmentFlag.AlignHCenter
        )
        cover_btn_layout = QHBoxLayout()
        self._load_cover_button = QPushButton("Load…")
        self._clear_cover_button = QPushButton("Clear")
        self._fetch_cover_button = QPushButton("Fetch Online")
        cover_btn_layout.addWidget(self._load_cover_button)
        cover_btn_layout.addWidget(self._clear_cover_button)
        cover_btn_layout.addWidget(self._fetch_cover_button)
        cover_layout.addLayout(cover_btn_layout)
        cover_group.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        editor_layout.addWidget(cover_group)

        # Right: tag editor (scrollable form)
        tag_group = QGroupBox("Tags")
        tag_outer = QVBoxLayout(tag_group)
        tag_outer.setContentsMargins(0, 4, 0, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_contents = QWidget()
        form = QFormLayout(scroll_contents)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setSpacing(6)
        form.setContentsMargins(8, 4, 8, 4)

        visible_fields = self._settings.visible_fields()
        for field_key, label_text, attr_name, placeholder in self._FIELD_DEFS:
            label = QLabel(label_text)
            edit = QLineEdit()
            if placeholder:
                edit.setPlaceholderText(placeholder)
            form.addRow(label, edit)
            self._field_widgets[field_key] = (label, edit)
            setattr(self, attr_name, edit)
            visible = field_key in visible_fields
            label.setVisible(visible)
            edit.setVisible(visible)

        # "Apply to selected" checkbox
        self._apply_to_selected_check = QCheckBox("Apply to selected tracks")
        form.addRow("", self._apply_to_selected_check)

        scroll.setWidget(scroll_contents)
        tag_outer.addWidget(scroll)
        editor_layout.addWidget(tag_group, stretch=1)
        root_layout.addLayout(editor_layout, stretch=1)

        # ── Action buttons ────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        self._open_button = QPushButton("Open Files…")
        self._save_button = QPushButton("Save Tags")
        self._rename_button = QPushButton("Rename Files…")
        self._regex_button = QPushButton("Find & Replace…")
        for btn in (
            self._open_button, self._save_button,
            self._rename_button, self._regex_button,
        ):
            btn_layout.addWidget(btn)
        root_layout.addLayout(btn_layout)

        # ── Audio Player (Milestone 2) ──────────────────────────────────────────
        player_group = QGroupBox("Audio Preview")
        player_layout = QVBoxLayout(player_group)
        self._audio_player = AudioPlayer()
        player_layout.addWidget(self._audio_player)
        root_layout.addWidget(player_group)

        # ── Status bar ────────────────────────────────────────────────
        self.statusBar().showMessage("Ready")

        # ── Menu bar ─────────────────────────────────────────────────
        self._build_menus()

    def _build_menus(self) -> None:
        mb = self.menuBar()

        # ── File ──────────────────────────────────────────────────────────
        file_menu = mb.addMenu("File")
        file_menu.setObjectName("fileMenu")
        _a(file_menu, "Open Files…",             self._open_files,    "Ctrl+O")
        _a(file_menu, "Save Tags",               self._save_tags,     "Ctrl+S")
        file_menu.addSeparator()

        # Open Recent submenu
        self._recent_menu = file_menu.addMenu("Open Recent")
        self._recent_menu.setObjectName("recentMenu")
        self._update_recent_menu()

        file_menu.addSeparator()
        export_menu = file_menu.addMenu("Export Tracklist")
        _a(export_menu, "CSV Report…",  lambda: self._export_tracklist("csv"))
        _a(export_menu, "HTML Report…", lambda: self._export_tracklist("html"))
        
        file_menu.addSeparator()
        _a(file_menu, "Import CSV…",             self._import_csv)
        _a(file_menu, "Import iTunes Library…",  self._import_itunes)
        _a(file_menu, "Import MusicBee Library…",self._import_musicbee)

        # iTunes Export — enabled only after a library has been imported
        self._export_itunes_action = _a(
            file_menu, "Export Changes to iTunes…", self._export_itunes_sync
        )
        self._export_itunes_action.setEnabled(False)

        file_menu.addSeparator()
        _a(file_menu, "Exit", self.close, "Ctrl+Q")

        # ── Edit ──────────────────────────────────────────────────────────
        edit_menu = mb.addMenu("Edit")
        edit_menu.setObjectName("editMenu")
        _a(edit_menu, "Find & Replace…",  self._regex_find_replace)
        edit_menu.addSeparator()

        # Case Correction submenu
        case_menu = edit_menu.addMenu("Case Correction")
        case_menu.setObjectName("caseMenu")
        _a(case_menu, "Title Case",  lambda: self._apply_case_correction("title"))
        _a(case_menu, "UPPER CASE",  lambda: self._apply_case_correction("upper"))
        _a(case_menu, "lower case",  lambda: self._apply_case_correction("lower"))

        edit_menu.addSeparator()
        self._undo_action = self._undo_stack.createUndoAction(self, "Undo")
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(self._undo_action)

        self._redo_action = self._undo_stack.createRedoAction(self, "Redo")
        self._redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(self._redo_action)

        edit_menu.addSeparator()
        _a(edit_menu, "Settings…", self._open_settings)

        # ── Automation ────────────────────────────────────────────────────
        auto_menu = mb.addMenu("Automation")
        auto_menu.setObjectName("autoMenu")
        _a(auto_menu, "Tag from Filename…", self._tag_from_filename)
        _a(auto_menu, "Batch Rename from Tags…", self._batch_rename)
        auto_menu.addSeparator()
        _a(auto_menu, "Number Track(s) Sequentially", self._auto_number_tracks)
        _a(auto_menu, "Bulk Edit Metadata…", self._bulk_edit_selected)

        # ── Online ────────────────────────────────────────────────────────
        online_menu = mb.addMenu("Online")
        online_menu.setObjectName("onlineMenu")
        _a(online_menu, "Fetch Album Metadata (MusicBrainz)…", self._fetch_album_metadata)
        _a(online_menu, "Fetch Cover Art (Discogs)…",         self._fetch_cover_online)
        _a(online_menu, "Optimize Selected Covers…",         self._optimize_selected_covers)
        _a(online_menu, "Search Discogs Release…",           self._search_discogs)
        _a(online_menu, "Search Audiobook (Audnexus)…",      self._search_audiobook)

        # ── Help ──────────────────────────────────────────────────────────
        help_menu = mb.addMenu("Help")
        help_menu.setObjectName("helpMenu")
        _a(help_menu, "About MetaTag…",             self._show_about)

    # ─────────────────────────────────────────────────────────────────────
    # Signal wiring
    # ─────────────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        # Buttons
        self._open_button.clicked.connect(self._open_files)
        self._save_button.clicked.connect(self._save_tags)
        self._regex_button.clicked.connect(self._regex_find_replace)
        self._rename_button.clicked.connect(self._batch_rename)
        self._fetch_cover_button.clicked.connect(self._fetch_cover_online)
        self._load_cover_button.clicked.connect(self._load_cover)
        self._clear_cover_button.clicked.connect(self._clear_cover)

        # Navigation
        self._prev_button.clicked.connect(self._prev_track)
        self._next_button.clicked.connect(self._next_track)
        QShortcut(QKeySequence(Qt.Key.Key_Left),  self).activated.connect(self._prev_track)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self).activated.connect(self._next_track)

        # Search Bar
        self._search_edit.textChanged.connect(self._proxy_model.setFilterFixedString)

        # Delete / Backspace → remove selected tracks from list (not from disk)
        QShortcut(QKeySequence(Qt.Key.Key_Delete),    self._file_list).activated.connect(self._remove_selected_tracks)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace), self._file_list).activated.connect(self._remove_selected_tracks)

        # File list selection (Model/View uses selectionModel)
        self._file_list.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Right-click context menu
        self._file_list.customContextMenuRequested.connect(self._show_context_menu)

        # Cover art drop
        self._cover_label.coverDropped.connect(self._cover_dropped)
        self._cover_label.imageDropped.connect(self._cover_image_dropped)
        self._cover_label.urlDropped.connect(self._cover_url_dropped)

        # Tag field edits — data-driven via lambda captures
        for field_key, _, attr_name, _ in self._FIELD_DEFS:
            edit: QLineEdit = getattr(self, attr_name)
            edit.textChanged.connect(
                lambda text, fk=field_key: self._on_field_text_changed(fk, text)
            )

    # ─────────────────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _prev_track(self) -> None:
        if not self._tracks:
            return
        # Get current proxy row
        current_proxy_row = -1
        selected = self._file_list.selectionModel().selectedRows()
        if selected:
            current_proxy_row = selected[0].row()
        
        new_proxy_row = max(0, current_proxy_row - 1)
        self._file_list.selectRow(new_proxy_row)

    @Slot()
    def _next_track(self) -> None:
        if not self._tracks:
            return
        # Get current proxy row
        current_proxy_row = -1
        selected = self._file_list.selectionModel().selectedRows()
        if selected:
            current_proxy_row = selected[0].row()

        new_proxy_row = min(self._proxy_model.rowCount() - 1, current_proxy_row + 1)
        self._file_list.selectRow(new_proxy_row)

    def _update_nav_label(self) -> None:
        """Refresh the N / Total navigation label from current state."""
        total = len(self._tracks)
        if total == 0 or self._current_index < 0:
            self._nav_label.setText("0 / 0")
        else:
            self._nav_label.setText(f"{self._current_index + 1} / {total}")

    def _on_selection_changed(self, selected, deselected) -> None:
        """Handle track selection change in the QTableView."""
        indexes = self._file_list.selectionModel().selectedRows()
        if not indexes:
            self._current_index = -1
            self._update_nav_label()
            self._clear_editor()
            return

        # Use the first selected row as the 'current' one for the editor
        proxy_index = indexes[0]
        source_index = self._proxy_model.mapToSource(proxy_index)
        self._current_index = source_index.row()
        track = self._tracks[self._current_index]
        self._load_track(self._current_index)
        self._audio_player.load_track(track.file_path)
        self._update_nav_label()

    # ─────────────────────────────────────────────────────────────────────
    # Track removal (Delete / Backspace / context menu)
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _remove_selected_tracks(self) -> None:
        """Remove selected rows from both self._tracks and the view."""
        indexes = self._file_list.selectionModel().selectedRows()
        if not indexes:
            return
            
        # Map proxy indices to source row indices
        source_rows = sorted(
            [self._proxy_model.mapToSource(idx).row() for idx in indexes],
            reverse=True
        )
        
        self._track_model.beginResetModel()
        for row in source_rows:
            if 0 <= row < len(self._tracks):
                self._tracks.pop(row)
        self._track_model.endResetModel()
        
        self._current_index = -1
        self._update_nav_label()
        self._clear_editor()
        self.statusBar().showMessage(f"Removed {len(source_rows)} track(s) from list", 3000)

        # Reset current selection
        total = len(self._tracks)
        if total == 0:
            self._current_index = -1
            self._clear_editor()
        else:
            self._current_index = min(source_rows[-1], total - 1)
            self._file_list.selectRow(self._current_index)
            self._load_track(self._current_index)

        self._update_nav_label()

    # ─────────────────────────────────────────────────────────────────────
    # Context menu
    # ─────────────────────────────────────────────────────────────────────

    @Slot(QPoint)
    def _show_context_menu(self, pos: QPoint) -> None:
        rows = self._get_selected_rows()
        if not rows:
            return

        menu = QMenu(self)

        # ── Number tracks sequentially (always available) ──────────────────
        num_action = menu.addAction(f"Number {len(rows)} Track(s) Sequentially")
        num_action.triggered.connect(self._auto_number_tracks)

        # ── Bulk edit (always available) ─────────────────────────────
        bulk_action = menu.addAction(f"Bulk Edit {len(rows)} Track(s)…")
        bulk_action.triggered.connect(self._bulk_edit_selected)
        menu.addSeparator()

        # Browse folder — only when a single track is selected
        if len(rows) == 1:
            row = next(iter(rows))
            if 0 <= row < len(self._tracks):
                track = self._tracks[row]
                browse_action = menu.addAction("Browse Containing Folder")
                browse_action.triggered.connect(
                    lambda: self._browse_folder(track.file_path)
                )
            menu.addSeparator()
            search_action = menu.addAction("Search Discogs…")
            search_action.triggered.connect(self._search_discogs)
            menu.addSeparator()

        remove_action = menu.addAction(f"Remove {len(rows)} Track(s) from List")
        remove_action.triggered.connect(self._remove_selected_tracks)

        menu.exec(self._file_list.viewport().mapToGlobal(pos))

    def _auto_number_tracks(self) -> None:
        """Number the selected tracks sequentially (1, 2, 3…) by their current
        visual order in the table, then refresh the editor."""
        # Collect selected proxy rows in visual order, then map to source
        proxy_indexes = sorted(
            self._file_list.selectionModel().selectedRows(),
            key=lambda idx: idx.row()
        )
        source_rows = [self._proxy_model.mapToSource(idx).row() for idx in proxy_indexes]

        if not source_rows:
            return

        self._undo_stack.beginMacro(f"Number {len(source_rows)} track(s) sequentially")
        for sequence_num, row in enumerate(source_rows, start=1):
            if 0 <= row < len(self._tracks):
                track = self._tracks[row]
                if track.track_number != sequence_num:
                    cmd = TagEditCommand(
                        self, [row], "track_number", str(sequence_num),
                        f"Set track #{sequence_num}"
                    )
                    self._undo_stack.push(cmd)
        self._undo_stack.endMacro()

        # Refresh the track model display
        self._track_model.beginResetModel()
        self._track_model.endResetModel()

        # Reload editor for current track so the field updates immediately
        if 0 <= self._current_index < len(self._tracks):
            self._load_track(self._current_index)

        self.statusBar().showMessage(
            f"Numbered {len(source_rows)} track(s) sequentially", 3000
        )

    def _browse_folder(self, file_path: Path) -> None:
        """Open the file's parent directory in Windows Explorer."""
        import subprocess
        try:
            # /select,<path> (no space) highlights the file in Explorer
            subprocess.Popen(["explorer", f"/select,{file_path}"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder:\n{e}")

    # ─────────────────────────────────────────────────────────────────────
    # Bulk Edit
    # ─────────────────────────────────────────────────────────────────────

    def _bulk_edit_selected(self) -> None:
        """Open the Bulk Edit dialog and apply the chosen fields to all
        selected tracks as a single, undo-able macro operation."""
        # Collect selected source rows
        proxy_indexes = self._file_list.selectionModel().selectedRows()
        source_rows = sorted(
            {self._proxy_model.mapToSource(idx).row() for idx in proxy_indexes}
        )
        if not source_rows:
            return

        dlg = BulkEditDialog(n_tracks=len(source_rows), parent=self)
        if dlg.exec() != BulkEditDialog.DialogCode.Accepted:
            return

        fields = dlg.get_field_values()   # {field_key: value_str}
        if not fields:
            return

        self._undo_stack.beginMacro(
            f"Bulk edit {len(fields)} field(s) on {len(source_rows)} track(s)"
        )
        for field_key, value in fields.items():
            cmd = TagEditCommand(
                self,
                source_rows,
                field_key,
                value,
                f"Bulk set {field_key}",
            )
            self._undo_stack.push(cmd)
        self._undo_stack.endMacro()

        # Refresh model display and current editor
        self._track_model.beginResetModel()
        self._track_model.endResetModel()
        if 0 <= self._current_index < len(self._tracks):
            self._load_track(self._current_index)

        self.statusBar().showMessage(
            f"Bulk edit: set {len(fields)} field(s) on {len(source_rows)} track(s)", 4000
        )

    # ─────────────────────────────────────────────────────────────────────
    # Case Correction
    # ─────────────────────────────────────────────────────────────────────

    @Slot(str)
    def _apply_case_correction(self, mode: str) -> None:
        """Apply title/upper/lower case to text fields of selected (or current) tracks.

        Applies to string fields only (artist, album, title, genre, composer,
        grouping, comment).  Numeric fields (year, bpm, track#, disc#) are left
        untouched.
        """
        _text_fields = ("artist", "album", "title", "genre", "composer", "grouping", "comment")
        fn = {"title": to_title_case, "upper": to_upper, "lower": to_lower}.get(mode)
        if fn is None:
            return

        targets: list[int] = []
        if self._apply_to_selected_check.isChecked():
            targets = sorted(self._get_selected_rows())
        elif 0 <= self._current_index < len(self._tracks):
            targets = [self._current_index]

        modified = 0
        for row in targets:
            if 0 <= row < len(self._tracks):
                track = self._tracks[row]
                for field in _text_fields:
                    old_val = getattr(track, field, "")
                    new_val = fn(old_val)
                    if new_val != old_val:
                        setattr(track, field, new_val)
                        modified += 1

        if modified and 0 <= self._current_index < len(self._tracks):
            self._load_track(self._current_index)
        self.statusBar().showMessage(
            f"Case correction applied to {len(targets)} track(s)", 3000
        )

    # ─────────────────────────────────────────────────────────────────────
    # Open Recent
    # ─────────────────────────────────────────────────────────────────────

    def _update_recent_menu(self) -> None:
        """Rebuild the Open Recent submenu from saved settings."""
        if self._recent_menu is None:
            return
        self._recent_menu.clear()
        folders = self._settings.recent_folders()
        if not folders:
            no_action = self._recent_menu.addAction("(No Recent Folders)")
            no_action.setEnabled(False)
            return
        for folder in folders:
            action = self._recent_menu.addAction(folder)
            action.triggered.connect(
                lambda checked=False, f=folder: self._open_recent_folder(f)
            )
        self._recent_menu.addSeparator()
        clear_action = self._recent_menu.addAction("Clear Recent")
        clear_action.triggered.connect(self._clear_recent)

    def _open_recent_folder(self, folder: str) -> None:
        """Load all audio files from a recently-opened folder."""
        path = Path(folder)
        if not path.is_dir():
            QMessageBox.warning(self, "Folder Not Found",
                                f"The folder no longer exists:\n{folder}")
            return
        files = find_audio_files(folder, recursive=self._settings.recursive_search())
        if files:
            self._open_files(files)
        else:
            self.statusBar().showMessage("No audio files found in that folder", 3000)

    def _clear_recent(self) -> None:
        self._settings.clear_recent_folders()
        self._update_recent_menu()

    # ─────────────────────────────────────────────────────────────────────
    # iTunes Export (real round-trip)
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _export_itunes_sync(self) -> None:
        """Export all loaded track changes back to the iTunes Library XML."""
        if not self._last_itunes_xml:
            QMessageBox.warning(self, "No Library",
                                "No iTunes Library has been imported in this session.")
            return
        if not self._tracks:
            QMessageBox.warning(self, "No Tracks", "No tracks are loaded.")
            return
        from ..import_io.itunes_sync import export_changes
        ok = export_changes(self._tracks, self._last_itunes_xml)
        if ok:
            QMessageBox.information(
                self, "Export Complete",
                f"Changes exported to:\n{self._last_itunes_xml}\n\n"
                "A .bak backup was created automatically.\n"
                "Re-import the library in iTunes to see the updates."
            )
            self.statusBar().showMessage("iTunes library updated successfully", 5000)
        else:
            QMessageBox.warning(self, "Export Failed",
                                "Could not export changes. Check the log for details.")

    # ─────────────────────────────────────────────────────────────────────
    # Field helpers (data-driven)
    # ─────────────────────────────────────────────────────────────────────

    def _clear_editor(self) -> None:
        """Clear all editor fields and reset the cover preview."""
        self._block_all_signals(True)
        for _, _, attr_name, _ in self._FIELD_DEFS:
            getattr(self, attr_name).clear()
        self._block_all_signals(False)
        self._cover_label.clear()
        self._audio_player.stop()

    def _block_all_fields(self, blocked: bool) -> None:
        for _, edit in self._field_widgets.values():
            edit.blockSignals(blocked)

    def _get_field_display(self, track: Track, field_key: str) -> str:
        """Return the display string for a field, handling X/Y formatting."""
        if field_key == "track_number":
            val = str(track.track_number) if track.track_number > 0 else ""
            if track.track_total > 0:
                val = f"{track.track_number}/{track.track_total}"
            return val
        if field_key == "disc_number":
            val = str(track.disc_number) if track.disc_number > 0 else ""
            if track.disc_total > 0:
                val = f"{track.disc_number}/{track.disc_total}"
            return val
        if field_key in ("year", "bpm"):
            v = getattr(track, field_key, 0)
            return str(v) if v > 0 else ""
        return str(getattr(track, field_key, ""))

    @Slot(str)
    def _field_changed(self, field_key: str, text: str) -> None:
        """Generic slot: update current or selected tracks when any field edits.

        FIX #7: track_number and disc_number support "N/T" strings in the UI.
        We decompose them here into separate number + total commands so that
        the undo system (which stores plain ints) never silently drops the total.
        """
        indexes = self._file_list.selectionModel().selectedRows()
        targets = [self._proxy_model.mapToSource(idx).row() for idx in indexes]

        if not targets and 0 <= self._current_index < len(self._tracks):
            targets = [self._current_index]

        if not targets:
            return

        _NUM_TOTAL_FIELDS = {
            "track_number": "track_total",
            "disc_number":  "disc_total",
        }

        if field_key in _NUM_TOTAL_FIELDS:
            total_field = _NUM_TOTAL_FIELDS[field_key]
            parts = text.strip().split("/")
            num_str   = parts[0].strip()
            total_str = parts[1].strip() if len(parts) > 1 else ""
            # Push as a macro so Undo treats both as one action
            self._undo_stack.beginMacro(f"Edit {field_key}")
            self._undo_stack.push(TagEditCommand(self, targets, field_key,   num_str))
            self._undo_stack.push(TagEditCommand(self, targets, total_field, total_str))
            self._undo_stack.endMacro()
        else:
            self._undo_stack.push(TagEditCommand(self, targets, field_key, text))

    @Slot(str)
    def _on_field_text_changed(self, field_key: str, text: str) -> None:
        """Wrapper that updates track data then restarts the auto-save debounce."""
        self._field_changed(field_key, text)
        if self._tracks and self._current_index >= 0 and self._settings.auto_save_enabled():
            self._auto_save_timer.start()

    def _get_selected_rows(self) -> set[int]:
        """Return the set of currently selected row indices in the file list."""
        return {self._proxy_model.mapToSource(idx).row() for idx in self._file_list.selectedIndexes()}

    # ─────────────────────────────────────────────────────────────────────
    # Track loading / unloading
    # ─────────────────────────────────────────────────────────────────────

    @Slot(int)
    def _on_row_changed(self, visual_row: int) -> None:
        """Legacy slot — kept for compatibility; actual selection is handled
        by _on_selection_changed via selectionModel.selectionChanged."""
        pass

    def _load_track(self, index: int) -> None:
        """Load track metadata into the editor."""
        track = self._tracks[index]
        if not track.is_loaded:
            if not track.load():
                self._clear_editor()
                self.statusBar().showMessage(
                    f"Failed to load: {track.file_path.name}", 4000
                )
                return

        self._block_all_signals(True)
        for field_key, _, attr_name, _ in self._FIELD_DEFS:
            edit: QLineEdit = getattr(self, attr_name)
            edit.setText(self._get_field_display(track, field_key))
        self._block_all_signals(False)

        # Cover art
        self._cover_label.setCoverImage(track.cover_art, track.album)

        dur_s = track.duration // 1000
        dur_str = f"{dur_s // 60}:{dur_s % 60:02d}" if dur_s > 0 else "?"
        self.statusBar().showMessage(
            f"{track.file_path.name}  ·  {dur_str}", 4000
        )

    def _block_all_signals(self, block: bool) -> None:
        """Block all field-edit signals to avoid loops during loading."""
        for _, _, attr_name, _ in self._FIELD_DEFS:
            getattr(self, attr_name).blockSignals(block)

    # ─────────────────────────────────────────────────────────────────────
    # File operations
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _open_files(self, file_paths: "list[str] | None" = None) -> None:
        """Open files — always replaces the current session (menu/button action)."""
        if file_paths is None:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select audio files",
                "",
                "Audio files (*.mp3 *.flac *.wav *.aiff *.ogg *.m4a *.mp4 "
                "*.opus *.wma *.oga *.spx *.m4b *.m4p)",
            )
            if not files:
                return
        else:
            files = list(file_paths)

        self._track_model.beginResetModel()
        self._tracks.clear()
        
        new_tracks = [Track(f) for f in files]
        for t in new_tracks:
            t.load()
            
        self._tracks.extend(new_tracks)
        self._track_model.endResetModel()
        self._proxy_model.invalidate()
        self._file_list.viewport().update()

        if self._tracks:
            self._current_index = 0
            self._file_list.selectRow(0)
            self._load_track(0)
        else:
            self._current_index = -1

        self._update_nav_label()
        self.statusBar().showMessage(f"Loaded {len(files)} file(s)", 3000)

        # Save folder to recent list
        if files:
            folder = str(Path(files[0]).parent)
            self._settings.add_recent_folder(folder)
            self._update_recent_menu()

    def _add_files(self, file_paths: "list[str]") -> None:
        """Append files to the current session — used by drag-and-drop."""
        if not file_paths:
            return
        start = len(self._tracks)
        self._track_model.beginResetModel()
        
        new_tracks = [Track(f) for f in file_paths]
        for t in new_tracks:
            t.load()
            
        self._tracks.extend(new_tracks)
        self._track_model.endResetModel()
        self._proxy_model.invalidate()
        self._file_list.viewport().update()

        # Select the first newly-added track and immediately load its metadata
        # (selectRow fires selectionChanged, but the model reset can race it;
        #  explicit _load_track here guarantees the editor is populated)
        if start < len(self._tracks):
            self._current_index = start
            self._file_list.selectRow(start)
            self._load_track(start)
            self._audio_player.load_track(self._tracks[start].file_path)

        self._update_nav_label()
        self.statusBar().showMessage(
            f"Added {len(file_paths)} file(s)  ·  {len(self._tracks)} total", 3000
        )
        # Update recent folder from the dropped files
        folder = str(Path(file_paths[0]).parent)
        self._settings.add_recent_folder(folder)
        self._update_recent_menu()


    @Slot()
    def _save_tags(self) -> None:
        saved, failed, failed_names = 0, 0, []
        preserve = self._settings.preserve_timestamps()
        for track in self._tracks:
            if track.is_dirty:
                if track.save(preserve_timestamps=preserve):
                    saved += 1
                else:
                    failed += 1
                    failed_names.append(track.file_path.name)

        msg = f"Saved {saved} track(s)"
        if failed:
            msg += f", {failed} failed: {', '.join(failed_names)}"
        self.statusBar().showMessage(msg, 5000)

        if failed:
            QMessageBox.warning(
                self, "Save Errors",
                f"Failed to save {failed} track(s).\nCheck the status bar for details.",
            )

    # ─────────────────────────────────────────────────────────────────────
    # Cover art
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _load_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Art", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if path:
            self._set_cover_from_file(path)

    @Slot(str)
    def _cover_dropped(self, path: str) -> None:
        """Image dropped onto the cover art widget — always apply to all selected
        tracks so the user doesn't need to tick the checkbox first."""
        self._set_cover_from_file(path, apply_to_all_selected=True)

    @Slot(object)
    def _cover_image_dropped(self, image: Image.Image) -> None:
        self._set_cover_from_image(image, apply_to_all_selected=True)

    @Slot(str)
    def _cover_url_dropped(self, url: str) -> None:
        self._download_cover_url(url)

    def _set_cover_from_file(self, path: str, apply_to_all_selected: bool = False) -> None:
        try:
            image = Image.open(path)
            self._set_cover_from_image(image, apply_to_all_selected)
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load image: {e}")

    def _set_cover_from_image(self, image: Image.Image, apply_to_all_selected: bool = False) -> None:
        try:
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")

            # Apply to selected rows if: the checkbox is ticked, OR the caller
            # explicitly requested it (e.g. a drop onto the cover art widget).
            selected_rows = [
                self._proxy_model.mapToSource(idx).row()
                for idx in self._file_list.selectionModel().selectedRows()
            ]
            if apply_to_all_selected or self._apply_to_selected_check.isChecked():
                target_rows = [r for r in selected_rows if 0 <= r < len(self._tracks)]
            elif 0 <= self._current_index < len(self._tracks):
                target_rows = [self._current_index]
            else:
                target_rows = []

            if target_rows:
                target_tracks = [self._tracks[r] for r in target_rows]
                cmd = CoverChangeCommand(self, target_tracks, image,
                                         f"Set cover art ({len(target_rows)} track(s))")
                self._undo_stack.push(cmd)
                self._cover_label.setCoverImage(image)
                self.statusBar().showMessage(
                    f"Cover applied to {len(target_rows)} track(s)", 3000
                )
            else:
                self._cover_label.setCoverImage(image)
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to set image: {e}")

    @Slot()
    def _clear_cover(self) -> None:
        target_rows = []
        if self._apply_to_selected_check.isChecked():
            # FIX #6: map proxy rows to source rows before indexing _tracks
            for idx in self._file_list.selectionModel().selectedRows():
                row = self._proxy_model.mapToSource(idx).row()
                if 0 <= row < len(self._tracks):
                    target_rows.append(row)
        elif 0 <= self._current_index < len(self._tracks):
            target_rows = [self._current_index]

        if target_rows:
            target_tracks = [self._tracks[r] for r in target_rows]
            cmd = CoverChangeCommand(self, target_tracks, None,
                                     f"Clear cover art ({len(target_rows)} track(s))")
            self._undo_stack.push(cmd)
            self._cover_label.setCoverImage(None)
            self.statusBar().showMessage(
                f"Cover cleared from {len(target_rows)} track(s)", 3000
            )

    @Slot()
    def _fetch_cover_online(self) -> None:
        if self._current_index < 0 or self._current_index >= len(self._tracks):
            QMessageBox.warning(self, "No Track", "No track selected.")
            return

        track = self._tracks[self._current_index]
        artist, album = track.artist.strip(), track.album.strip()
        if not artist and not album:
            QMessageBox.warning(
                self, "Missing Info",
                "Artist and album are both empty. Please fill in at least one.",
            )
            return

        from ..online.cover_finder import CoverFinder
        if self._cover_finder is None:
            self._cover_finder = CoverFinder(self)
            self._cover_finder.set_base_url(self._settings.musicbrainz_url())
            self._cover_finder.cover_fetched.connect(self._on_cover_fetched)
            self._cover_finder.fetch_error.connect(self._on_cover_fetch_error)

        self.statusBar().showMessage(f"Looking up cover for {artist} - {album}…")
        self._cover_finder.set_base_url(self._settings.musicbrainz_url())
        self._cover_finder.fetch_cover(artist, album)

    def _on_cover_fetched(self, qimage) -> None:
        if self._cover_finder:
            pil_image = self._cover_finder.qimage_to_pil(qimage)
        else:
            from ..online.cover_finder import CoverFinder
            pil_image = CoverFinder().qimage_to_pil(qimage)

        if 0 <= self._current_index < len(self._tracks):
            track = self._tracks[self._current_index]
            track.cover_art = pil_image
            # Adaptive resizing
            track.optimize_cover(max_size=self._settings.cover_max_res())
            
            self._cover_label.setCoverImage(track.cover_art, track.album)
            self.statusBar().showMessage("Cover art fetched and optimized successfully", 3000)

    def _on_cover_fetch_error(self, error_msg: str) -> None:
        QMessageBox.warning(self, "Fetch Error", error_msg)
        self.statusBar().showMessage(f"Cover fetch failed: {error_msg}", 5000)

    # ─────────────────────────────────────────────────────────────────────
    # Rename / regex
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _batch_rename(self) -> None:
        """Rename selected tracks based on their metadata using BatchRenameDialog."""
        indexes = self._file_list.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "No Selection", "Please select tracks to rename.")
            return

        tracks = [self._tracks[self._proxy_model.mapToSource(idx).row()] for idx in indexes]
        dialog = BatchRenameDialog(self, tracks)

        if dialog.exec():
            pattern = dialog.pattern()
            success = 0
            for idx in [self._proxy_model.mapToSource(i).row() for i in indexes]:
                track = self._tracks[idx]
                tags = {
                    "artist": track.artist, "album": track.album, "title": track.title,
                    "track_number": track.track_number, "disc_number": track.disc_number,
                    "year": track.year,
                }
                new_name = format_filename(tags, pattern) + track.file_path.suffix
                new_path = track.file_path.parent / new_name
                try:
                    track.file_path.rename(new_path)
                    # FIX #5: file_path is a read-only property; use update_path()
                    track.update_path(new_path)
                    self._track_model.update_row(idx)
                    success += 1
                except Exception as e:
                    print(f"Failed to rename {track.file_path}: {e}")

            self.statusBar().showMessage(f"Renamed {success} of {len(tracks)} tracks", 5000)

    @Slot()
    def _regex_find_replace(self) -> None:
        from .regex_dialog import RegexDialog
        from ..utils.regex_utils import apply_regex_to_fields

        dialog = RegexDialog(self)
        if dialog.exec():
            pattern = dialog.pattern()
            replacement = dialog.replacement()
            fields = dialog.selected_fields()
            case_sensitive = dialog.case_sensitive()
            modified = 0
            for track in self._tracks:
                fdict = {
                    k: getattr(track, k, "")
                    for k in ("artist", "album", "title", "genre",
                              "comment", "composer", "grouping")
                }
                new_fdict = apply_regex_to_fields(
                    fdict, pattern, replacement, fields, case_sensitive
                )
                for key in fields:
                    if fdict.get(key) != new_fdict.get(key):
                        # Wrap in Undo command
                        self._undo_stack.push(TagEditCommand(self, [self._tracks.index(track)], key, new_fdict[key]))
                        modified += 1
            if modified:
                self.statusBar().showMessage(
                    f"Applied regex to {modified} field(s)", 5000
                )
                if 0 <= self._current_index < len(self._tracks):
                    self._load_track(self._current_index)
            else:
                self.statusBar().showMessage("No changes made", 3000)

    # ─────────────────────────────────────────────────────────────────────
    # Utilities & Export (Milestone 5)
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _optimize_selected_covers(self) -> None:
        """Batch resize and strip metadata from selected covers."""
        indexes = self._file_list.selectionModel().selectedRows()
        if not indexes:
            return
            
        source_indices = [self._proxy_model.mapToSource(i).row() for i in indexes]
        success = 0
        max_res = self._settings.cover_max_res()
        for idx in source_indices:
            if self._tracks[idx].optimize_cover(max_size=max_res):
                success += 1
                
        if success:
            self._track_model.refresh() # Update icons if needed
            self.statusBar().showMessage(f"Optimized {success} cover(s)", 5000)
            if self._current_index in source_indices:
                self._load_track(self._current_index)

    def _export_tracklist(self, fmt: str) -> None:
        """Export current tracklist to CSV or HTML."""
        if not self._tracks:
            return
            
        ext = "csv" if fmt == "csv" else "html"
        filter_str = f"{fmt.upper()} files (*.{ext})"
        path, _ = QFileDialog.getSaveFileName(self, f"Export {fmt.upper()}", "", filter_str)
        
        if path:
            p = Path(path)
            res = False
            if fmt == "csv":
                res = exporter.export_csv(self._tracks, p)
            else:
                res = exporter.export_html(self._tracks, p)
                
            if res:
                self.statusBar().showMessage(f"Exported to {p.name}", 3000)
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to save file.")

    # ─────────────────────────────────────────────────────────────────────
    # Cloud APIs (Milestone 4)
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _fetch_album_metadata(self) -> None:
        """Query MusicBrainz for album metadata."""
        if not self._tracks:
            return
            
        # Use first selected or current track's info as seed
        track = self._tracks[self._current_index] if self._current_index >= 0 else self._tracks[0]
        artist, album = track.artist, track.album
        
        if not artist and not album:
            QMessageBox.warning(self, "No Info", "Please fill in Artist or Album to search.")
            return
            
        if self._mb_lookup is None:
            from ..online.musicbrainz_lookup import MusicBrainzLookup
            self._mb_lookup = MusicBrainzLookup(self)
            self._mb_lookup.set_base_url(self._settings.musicbrainz_url())
            self._mb_lookup.releases_fetched.connect(self._on_mb_releases_fetched)
            self._mb_lookup.lookup_error.connect(lambda e: self.statusBar().showMessage(f"Lookup error: {e}", 5000))
            
        self.statusBar().showMessage(f"Searching MusicBrainz for {artist} - {album}…")
        self._mb_lookup.lookup_release(artist, album)

    def _on_mb_releases_fetched(self, releases: List[Dict[str, Any]]) -> None:
        """Handle search results from MusicBrainz."""
        if not releases:
            return
            
        # If it's a list with one item that has 'tracks', it's the detail result.
        if len(releases) == 1 and "tracks" in releases[0]:
            self._apply_mb_metadata(releases[0])
            return

        # Show selection dialog
        dialog = PickReleaseDialog(self, releases)
        if dialog.exec():
            selected_id = dialog.selected_release_id()
            if selected_id:
                self.statusBar().showMessage("Fetching tracklist details…")
                self._mb_lookup.fetch_release_details(selected_id)

    def _apply_mb_metadata(self, data: Dict[str, Any]) -> None:
        """Map the fetched tracklist to the selected tracks in the UI."""
        indexes = self._file_list.selectionModel().selectedRows()
        if not indexes:
            # If nothing selected, just use the current view starting from first
            indexes = [self._proxy_model.index(i, 0) for i in range(self._proxy_model.rowCount())]
            
        source_indices = [self._proxy_model.mapToSource(i).row() for i in indexes]
        self._undo_stack.beginMacro(f"Fetch MusicBrainz: {data.get('title')}")
        
        # Map MusicBrainz tracks (1..N) to our selection
        mb_tracks = data.get("tracks", [])
        for i, idx in enumerate(source_indices):
            if i >= len(mb_tracks):
                break
                
            mb_t = mb_tracks[i]
            # Apply common album/artist to everyone
            self._undo_stack.push(TagEditCommand(self, [idx], "album", data.get("title")))
            self._undo_stack.push(TagEditCommand(self, [idx], "artist", mb_t.get("artist") or data.get("artist")))
            self._undo_stack.push(TagEditCommand(self, [idx], "title", mb_t.get("title")))
            self._undo_stack.push(TagEditCommand(self, [idx], "track_number", str(mb_t.get("number"))))
            
        self._undo_stack.endMacro()
        if 0 <= self._current_index < len(self._tracks):
            self._load_track(self._current_index)
        self.statusBar().showMessage("Successfully applied MusicBrainz metadata")

    @Slot()
    def _tag_from_filename(self) -> None:
        """Extract metadata from filenames for selected tracks."""
        # Get selected tracks
        indexes = self._file_list.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "No Selection", "Please select tracks to tag.")
            return

        tracks = [self._tracks[self._proxy_model.mapToSource(idx).row()] for idx in indexes]
        dialog = TagFromFilenameDialog(self, tracks)
        dialog._pattern_edit.setText(self._settings.filename_tag_pattern())
        
        if dialog.exec():
            pattern = dialog.pattern()
            self._settings.set_filename_tag_pattern(pattern)
            self._undo_stack.beginMacro(f"Tag From Filename: {pattern}")
            
            for idx in [self._proxy_model.mapToSource(i).row() for i in indexes]:
                track = self._tracks[idx]
                tags = parse_filename(track.file_path.stem, pattern)
                for field, value in tags.items():
                    self._undo_stack.push(TagEditCommand(self, [idx], field, value))
            
            self._undo_stack.endMacro()
            if 0 <= self._current_index < len(self._tracks):
                self._load_track(self._current_index)
            self.statusBar().showMessage(f"Applied pattern to {len(tracks)} tracks", 5000)

    # (duplicate _batch_rename removed — consolidated into the definition above)

    @Slot()
    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV files (*.csv)"
        )
        if path:
            from ..import_io.csv_io import import_csv
            tracks = import_csv(path)
            if tracks:
                self._track_model.beginResetModel()
                self._tracks.extend(tracks)
                self._track_model.endResetModel()
                self._update_nav_label()
                self.statusBar().showMessage(f"Imported {len(tracks)} track(s)", 3000)
            else:
                QMessageBox.warning(self, "Import Failed", "No tracks imported.")


    @Slot()
    def _import_itunes(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import iTunes Library", "",
            "iTunes Library (*.xml);;All files (*.*)"
        )
        if not path:
            return
        from ..import_io.itunes_sync import import_library
        tracks = import_library(path)
        if tracks:
            self._track_model.beginResetModel()
            self._tracks.extend(tracks)
            self._track_model.endResetModel()
            self._update_nav_label()
            # Store path and enable the export action
            self._last_itunes_xml = path
            if self._export_itunes_action is not None:
                self._export_itunes_action.setEnabled(True)
            self.statusBar().showMessage(
                f"Imported {len(tracks)} track(s) from iTunes", 3000
            )
        else:
            QMessageBox.warning(
                self, "Import Failed", "No tracks imported from iTunes library."
            )

    def _import_musicbee(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import MusicBee Library", "",
            "MusicBee Library (*.db);;All files (*.*)",
        )
        if not path:
            return
        from ..import_io.musicbee_sync import import_library
        tracks = import_library(path)
        if tracks:
            self._track_model.beginResetModel()
            self._tracks.extend(tracks)
            self._track_model.endResetModel()
            self._update_nav_label()
            self.statusBar().showMessage(
                f"Imported {len(tracks)} track(s) from MusicBee", 3000
            )
        else:
            QMessageBox.warning(
                self, "Import Failed", "No tracks imported from MusicBee library."
            )

    # ─────────────────────────────────────────────────────────────────────
    # Discogs
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _search_audiobook(self) -> None:
        """Open the audiobook search dialog and apply metadata."""
        if not self._tracks:
            QMessageBox.warning(self, "No Tracks", "Please load track(s) first.")
            return

        initial_query = ""
        if 0 <= self._current_index < len(self._tracks):
            track = self._tracks[self._current_index]
            initial_query = track.album or track.artist

        from .dialogs.audiobook_lookup_dialog import AudiobookLookupDialog
        dialog = AudiobookLookupDialog(self, initial_query=initial_query)
        if dialog.exec():
            book = dialog.get_selected_book()
            if not book:
                return

            # Map fields to selected tracks
            # Map Narrator -> Composer, Series -> Grouping
            modified = 0
            indexes = self._file_list.selectionModel().selectedRows()
            source_rows = [self._proxy_model.mapToSource(i).row() for i in indexes]
            
            # If no selection, apply to current track
            if not source_rows and 0 <= self._current_index < len(self._tracks):
                source_rows = [self._current_index]

            for row in source_rows:
                track = self._tracks[row]
                if book.get("title"): track.album = book["title"]
                if book.get("artist"): track.artist = book["artist"]
                if book.get("narrator"): track.composer = book["narrator"]
                if book.get("series_name"): track.grouping = book["series_name"]
                if book.get("year"): track.year = book["year"]
                if book.get("comment"): track.comment = book["comment"]
                modified += 1

            self.statusBar().showMessage(f"Applied audiobook metadata to {modified} track(s)", 5000)
            
            # Update UI and fetch cover if provided
            if 0 <= self._current_index < len(self._tracks):
                self._load_track(self._current_index)
            
            if book.get("cover_url"):
                self._download_cover_url(book["cover_url"])

    def _download_cover_url(self, url: str) -> None:
        """Helper to download and apply cover art from a URL."""
        if not url: return
        self.statusBar().showMessage("Downloading cover art…")
        
        # We can reuse the logic in CoverFinder if we make a small helper, 
        # but for now we'll do a quick internal download using NAM.
        from PySide6.QtNetwork import QNetworkRequest, QNetworkAccessManager
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QImage
        
        manager = QNetworkAccessManager(self)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0")
        
        reply = manager.get(request)
        def handle_reply():
            if reply.error() == 0:
                data = reply.readAll().data()
                qimg = QImage()
                if qimg.loadFromData(data):
                    from ..online.cover_finder import CoverFinder
                    # Use existing helper to convert to PIL
                    pil_img = CoverFinder().qimage_to_pil(qimg)
                    
                    if 0 <= self._current_index < len(self._tracks):
                        # Treat downloaded URL like a dragged image
                        self._set_cover_from_image(pil_img, apply_to_all_selected=True)
            else:
                self.statusBar().showMessage(f"Failed to download cover: {reply.errorString()}", 5000)
            reply.deleteLater()
            
        reply.finished.connect(handle_reply)
        # Keep manager alive
        self._temp_nam = manager 

    @Slot()
    def _search_discogs(self) -> None:
        if self._current_index < 0 or self._current_index >= len(self._tracks):
            QMessageBox.warning(self, "No Track", "No track selected.")
            return
        track = self._tracks[self._current_index]
        artist, album = track.artist.strip(), track.album.strip()
        if not artist and not album:
            QMessageBox.warning(
                self, "Missing Info",
                "Artist and album are both empty. Please fill in at least one.",
            )
            return
        from ..online.discogs_lookup import DiscogsLookup
        if self._discogs_lookup is None:
            self._discogs_lookup = DiscogsLookup(self)
            self._discogs_lookup.releases_fetched.connect(
                self._on_discogs_releases_fetched
            )
            self._discogs_lookup.lookup_error.connect(self._on_discogs_error)
        self.statusBar().showMessage(f"Searching Discogs for {artist} - {album}…")
        self._discogs_lookup.search_releases(artist, album)

    def _on_discogs_releases_fetched(self, releases: list) -> None:
        if not releases:
            self.statusBar().showMessage("No Discogs releases found", 3000)
            QMessageBox.information(self, "Discogs Search", "No releases found.")
            return
        self.statusBar().showMessage(f"Found {len(releases)} release(s) on Discogs", 3000)
        from .discogs_dialog import DiscogsDialog
        dialog = DiscogsDialog(releases, parent=self)
        dialog.release_selected.connect(self._apply_discogs_release)
        dialog.exec()

    def _apply_discogs_release(self, release: dict) -> None:
        """Populate current track tags from the selected Discogs release."""
        if self._current_index < 0 or self._current_index >= len(self._tracks):
            return
        track = self._tracks[self._current_index]
        if release.get("artist"):
            track.artist = release["artist"]
        if release.get("title"):
            track.album = release["title"]
        if release.get("year"):
            try:
                track.year = int(release["year"])
            except (ValueError, TypeError):
                pass
        if release.get("genre"):
            track.genre = release["genre"]
        # Refresh the editor with the new values
        self._load_track(self._current_index)
        self.statusBar().showMessage(
            f"Applied: {release.get('artist', '')} — {release.get('title', '')}", 4000
        )

    def _on_discogs_error(self, error_msg: str) -> None:
        QMessageBox.warning(self, "Discogs Error", error_msg)
        self.statusBar().showMessage(f"Discogs error: {error_msg}", 5000)

    # ─────────────────────────────────────────────────────────────────────
    # Settings / About
    # ─────────────────────────────────────────────────────────────────────

    @Slot()
    def _open_settings(self) -> None:
        from .settings_dialog import SettingsDialog
        # FIX #20: pass the shared settings instance so dialog and main window
        # always operate on the same object (not two separate QSettings wrappers).
        dialog = SettingsDialog(settings=self._settings, parent=self)
        if dialog.exec():
            # Refresh UI based on potentially changed settings
            visible_fields = self._settings.visible_fields()
            for field_key, (label, edit) in self._field_widgets.items():
                visible = field_key in visible_fields
                label.setVisible(visible)
                edit.setVisible(visible)
            
            # Update auto-save interval
            self._auto_save_timer.setInterval(self._settings.auto_save_interval())
            
            # Update online tokens if lookup modules exist
            if self._discogs_lookup:
                self._discogs_lookup.set_credentials(user_token=self._settings.discogs_token())
            if self._mb_lookup:
                self._mb_lookup.set_base_url(self._settings.musicbrainz_url())
            if self._cover_finder:
                self._cover_finder.set_base_url(self._settings.musicbrainz_url())

    @Slot()
    def _show_about(self) -> None:
        from .about_dialog import AboutDialog
        AboutDialog(version=get_version(), parent=self).exec()

    # ─────────────────────────────────────────────────────────────────────
    # Drag-and-drop (window level) — accepts both files and folders
    # ─────────────────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    # Accept if it is a directory or a supported audio file
                    if Path(path).is_dir():
                        event.setDropAction(Qt.DropAction.CopyAction)
                        event.acceptProposedAction()
                        return
                    if any(path.lower().endswith(ext) for ext in self._AUDIO_EXTENSIONS):
                        event.setDropAction(Qt.DropAction.CopyAction)
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if Path(path).is_dir() or any(
                        path.lower().endswith(ext) for ext in self._AUDIO_EXTENSIONS
                    ):
                        event.setDropAction(Qt.DropAction.CopyAction)
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        file_paths: List[str] = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if Path(path).is_dir():
                    # Find audio files inside the dropped folder (honor recursive setting)
                    recursive = self._settings.recursive_search()
                    file_paths.extend(find_audio_files(path, recursive=recursive))
                elif any(path.lower().endswith(ext) for ext in self._AUDIO_EXTENSIONS):
                    file_paths.append(path)

        if file_paths:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.acceptProposedAction()
            self._add_files(file_paths)  # append to session; _open_files replaces
        else:
            event.ignore()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _a(menu, text: str, slot, shortcut: str = "") -> QAction:
    """Create and add a QAction to *menu* with optional keyboard shortcut."""
    action = QAction(text, menu)
    action.triggered.connect(slot)
    if shortcut:
        action.setShortcut(QKeySequence(shortcut))
    menu.addAction(action)
    return action


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Application entry point."""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("--version", "-v"):
            print(f"MetaTag {get_version()}")
            return
        if arg in ("--help", "-h"):
            print("Usage: MetaTag [OPTION]")
            print("Metadata Editor (Batch audio metadata management)")
            print()
            print("Options:")
            print("  --help, -h        Show this help")
            return

    app = QApplication(sys.argv)
    app.setApplicationName("MetaTag")
    app.setOrganizationName("MetaTag")

    icon_path = _resource_path("img/logo.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # ── Dark theme ─────────────────────────────────────────────────────────
    app.setStyleSheet("""
        QMainWindow, QDialog, QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 9pt;
        }
        QMenuBar {
            background-color: #181825;
            color: #cdd6f4;
            border-bottom: 1px solid #313244;
        }
        QMenuBar::item:selected { background-color: #313244; }
        QMenu {
            background-color: #1e1e2e;
            color: #cdd6f4;
            border: 1px solid #45475a;
        }
        QMenu::item:selected { background-color: #313244; }
        QMenu::separator { height: 1px; background: #313244; margin: 2px 6px; }
        QTableWidget {
            background-color: #181825;
            alternate-background-color: #1e1e2e;
            gridline-color: #313244;
            color: #cdd6f4;
            selection-background-color: #45475a;
            selection-color: #cdd6f4;
            border: 1px solid #313244;
        }
        QHeaderView::section {
            background-color: #181825;
            color: #89b4fa;
            border: none;
            border-right: 1px solid #313244;
            border-bottom: 1px solid #313244;
            padding: 4px 6px;
            font-weight: bold;
        }
        QHeaderView::section:hover { background-color: #313244; }
        QLineEdit {
            background-color: #181825;
            color: #cdd6f4;
            border: 1px solid #313244;
            border-radius: 5px;
            padding: 4px 6px;
        }
        QLineEdit:focus { border: 1px solid #89b4fa; }
        QLineEdit#searchBar {
            background-color: #1e1e2e;
            border: 1px solid #45475a;
            border-radius: 8px;
            padding: 5px 10px;
            font-weight: 500;
        }
        QLineEdit#searchBar:focus {
            border: 1px solid #89b4fa;
            background-color: #181825;
        }
        QPushButton {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 5px 14px;
            min-width: 60px;
        }
        QPushButton:hover { background-color: #45475a; }
        QPushButton:pressed { background-color: #585b70; }
        QPushButton:default {
            border: 1px solid #89b4fa;
        }
        QGroupBox {
            border: 1px solid #313244;
            border-radius: 7px;
            margin-top: 10px;
            padding-top: 8px;
        }
        QGroupBox::title {
            color: #89b4fa;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QCheckBox { color: #cdd6f4; spacing: 6px; }
        QCheckBox::indicator {
            border: 1px solid #45475a;
            border-radius: 3px;
            width: 14px; height: 14px;
            background: #181825;
        }
        QCheckBox::indicator:checked { background: #89b4fa; }
        QScrollBar:vertical {
            background: #1e1e2e; width: 10px;
        }
        QScrollBar::handle:vertical {
            background: #45475a; border-radius: 5px; min-height: 20px;
        }
        QScrollBar::handle:vertical:hover { background: #585b70; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal {
            background: #1e1e2e; height: 10px;
        }
        QScrollBar::handle:horizontal {
            background: #45475a; border-radius: 5px; min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover { background: #585b70; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        QStatusBar {
            background-color: #181825;
            color: #a6adc8;
            border-top: 1px solid #313244;
        }
        QLabel { color: #cdd6f4; }
        QLabel#aboutSubtitle { color: #a6adc8; }
        QLabel#aboutVersion  { color: #585b70; }
        QLabel#aboutDesc     { color: #cdd6f4; }
        QLabel#aboutCredits  { color: #a6adc8; }
        QToolTip {
            background-color: #313244; color: #cdd6f4;
            border: 1px solid #45475a; border-radius: 4px;
            padding: 4px;
        }
    """)

    # ── Splash screen ──────────────────────────────────────────────────────
    splash: Optional[QSplashScreen] = None
    splash_path = _resource_path("img/splash.png")
    if splash_path.exists():
        splash_pixmap = QPixmap(str(splash_path))
        if not splash_pixmap.isNull():
            splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
            splash.show()
            app.processEvents()

    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.setWindowTitle(f"{PROJECT_NAME} — {SUBTITLE}")
    window.resize(980, 760)
    window.show()

    if splash is not None:
        # FIX #9: time.sleep() blocks the event loop; use a non-blocking QTimer instead
        QTimer.singleShot(3000, lambda: splash.finish(window))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
