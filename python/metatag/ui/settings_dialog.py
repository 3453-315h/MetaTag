"""Settings dialog for configurable UI and app behavior."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
    QTabWidget,
    QWidget,
    QFormLayout,
    QCheckBox,
    QSpinBox,
    QLineEdit,
)
from PySide6.QtCore import Qt

from ..core.config import FIELD_KEYS, Settings


class SettingsDialog(QDialog):
    """Multi-tabbed dialog for application configuration."""

    def __init__(self, settings: "Settings | None" = None, parent=None):
        super().__init__(parent)
        self._settings = settings if settings is not None else Settings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        self.setWindowTitle("Settings")
        self.resize(500, 600)

        main_layout = QVBoxLayout(self)
        self._tab_widget = QTabWidget()
        main_layout.addWidget(self._tab_widget)

        # ---- Tab 1: Editor (Field Visibility & Order) ----
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        editor_layout.addWidget(
            QLabel("Select and reorder fields to display in the tag editor:")
        )
        self._list_widget = QListWidget()
        self._list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        editor_layout.addWidget(self._list_widget)

        list_btn_layout = QHBoxLayout()
        self._move_up_button = QPushButton("Move Up")
        self._move_down_button = QPushButton("Move Down")
        self._select_all_button = QPushButton("Select All")
        self._deselect_all_button = QPushButton("Deselect All")
        list_btn_layout.addWidget(self._move_up_button)
        list_btn_layout.addWidget(self._move_down_button)
        list_btn_layout.addWidget(self._select_all_button)
        list_btn_layout.addWidget(self._deselect_all_button)
        editor_layout.addLayout(list_btn_layout)
        self._tab_widget.addTab(editor_tab, "Editor")

        # ---- Tab 2: General (Automation & Behavior) ----
        general_tab = QWidget()
        self._general_form = QFormLayout(general_tab)
        
        self._auto_save_check = QCheckBox("Enable auto-save tags")
        self._auto_save_interval = QSpinBox()
        self._auto_save_interval.setRange(100, 10000)
        self._auto_save_interval.setSuffix(" ms")
        self._auto_save_interval.setSingleStep(100)
        self._general_form.addRow("Auto-save:", self._auto_save_check)
        self._general_form.addRow("Auto-save delay:", self._auto_save_interval)

        self._preserve_time_check = QCheckBox("Preserve file modification time")
        self._general_form.addRow("File attributes:", self._preserve_time_check)

        self._restore_dir_check = QCheckBox("Restore last opened directory on startup")
        self._general_form.addRow("Startup:", self._restore_dir_check)
        
        self._tab_widget.addTab(general_tab, "General")

        # ---- Tab 3: Online (Metadata Services) ----
        online_tab = QWidget()
        self._online_form = QFormLayout(online_tab)
        
        self._discogs_token = QLineEdit()
        self._discogs_token.setPlaceholderText("Enter Personal Access Token…")
        self._discogs_token.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self._online_form.addRow("Discogs Token:", self._discogs_token)

        self._mb_url = QLineEdit()
        self._mb_url.setPlaceholderText("https://musicbrainz.org")
        self._online_form.addRow("MusicBrainz URL:", self._mb_url)

        self._cover_res = QSpinBox()
        self._cover_res.setRange(200, 4000)
        self._cover_res.setSuffix(" px")
        self._cover_res.setSingleStep(100)
        self._online_form.addRow("Max Cover Res:", self._cover_res)
        
        self._tab_widget.addTab(online_tab, "Online")

        # ---- Tab 4: Files ----
        files_tab = QWidget()
        self._files_form = QFormLayout(files_tab)
        
        self._recursive_check = QCheckBox("Recursive folder search")
        self._files_form.addRow("Search:", self._recursive_check)

        self._max_recent = QSpinBox()
        self._max_recent.setRange(1, 50)
        self._files_form.addRow("Max recent folders:", self._max_recent)
        
        self._tag_pattern = QLineEdit()
        self._tag_pattern.setPlaceholderText("%artist% - %title%")
        self._files_form.addRow("Default tag pattern:", self._tag_pattern)
        
        self._tab_widget.addTab(files_tab, "Files")

        # ---- Bottom Buttons ----
        dialog_buttons_layout = QHBoxLayout()
        self._reset_button = QPushButton("Reset to Defaults")
        self._ok_button = QPushButton("OK")
        self._cancel_button = QPushButton("Cancel")
        dialog_buttons_layout.addWidget(self._reset_button)
        dialog_buttons_layout.addStretch()
        dialog_buttons_layout.addWidget(self._ok_button)
        dialog_buttons_layout.addWidget(self._cancel_button)
        main_layout.addLayout(dialog_buttons_layout)

        # Wire up signals
        self._move_up_button.clicked.connect(self._move_up)
        self._move_down_button.clicked.connect(self._move_down)
        self._select_all_button.clicked.connect(self._select_all)
        self._deselect_all_button.clicked.connect(self._deselect_all)
        self._reset_button.clicked.connect(self._reset_to_defaults)
        self._ok_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)

    def _load_settings(self):
        """Load current settings into UI components."""
        # Page 1: Fields
        self._list_widget.clear()
        order = self._settings.field_order()
        visible_set = set(self._settings.visible_fields())
        for field in order:
            item = QListWidgetItem(self._field_display_name(field))
            item.setData(Qt.ItemDataRole.UserRole, field)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled 
                        | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled)
            item.setCheckState(Qt.CheckState.Checked if field in visible_set else Qt.CheckState.Unchecked)
            self._list_widget.addItem(item)

        # Page 2: General
        self._auto_save_check.setChecked(self._settings.auto_save_enabled())
        self._auto_save_interval.setValue(self._settings.auto_save_interval())
        self._preserve_time_check.setChecked(self._settings.preserve_timestamps())
        self._restore_dir_check.setChecked(self._settings.restore_last_dir())

        # Page 3: Online
        self._discogs_token.setText(self._settings.discogs_token())
        self._mb_url.setText(self._settings.musicbrainz_url())
        self._cover_res.setValue(self._settings.cover_max_res())

        # Page 4: Files
        self._recursive_check.setChecked(self._settings.recursive_search())
        self._max_recent.setValue(self._settings.max_recent_items())
        self._tag_pattern.setText(self._settings.filename_tag_pattern())

    def _field_display_name(self, field_key: str) -> str:
        names = {
            "artist": "Artist", "album": "Album", "title": "Title",
            "track_number": "Track Number", "year": "Year", "genre": "Genre",
            "disc_number": "Disc Number", "comment": "Comment",
            "composer": "Composer", "grouping": "Grouping", "bpm": "BPM",
        }
        return names.get(field_key, field_key)

    def _move_up(self):
        row = self._list_widget.currentRow()
        if row > 0:
            item = self._list_widget.takeItem(row)
            self._list_widget.insertItem(row - 1, item)
            self._list_widget.setCurrentRow(row - 1)

    def _move_down(self):
        row = self._list_widget.currentRow()
        if row < self._list_widget.count() - 1 and row >= 0:
            item = self._list_widget.takeItem(row)
            self._list_widget.insertItem(row + 1, item)
            self._list_widget.setCurrentRow(row + 1)

    def _select_all(self):
        for i in range(self._list_widget.count()):
            self._list_widget.item(i).setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        for i in range(self._list_widget.count()):
            self._list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)

    def _reset_to_defaults(self):
        reply = QMessageBox.question(
            self, "Reset Settings", "Reset all settings to factory defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._settings.reset_to_defaults()
            self._load_settings()

    def accept(self):
        # Save Editor Tab
        full_order = []
        visible_fields = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            field = item.data(Qt.ItemDataRole.UserRole)
            full_order.append(field)
            if item.checkState() == Qt.CheckState.Checked:
                visible_fields.append(field)
        self._settings.set_field_order(full_order)
        self._settings.set_visible_fields(visible_fields)

        # Save General Tab
        self._settings.set_auto_save_enabled(self._auto_save_check.isChecked())
        self._settings.set_auto_save_interval(self._auto_save_interval.value())
        self._settings.set_preserve_timestamps(self._preserve_time_check.isChecked())
        self._settings.set_restore_last_dir(self._restore_dir_check.isChecked())

        # Save Online Tab
        self._settings.set_discogs_token(self._discogs_token.text())
        self._settings.set_musicbrainz_url(self._mb_url.text())
        self._settings.set_cover_max_res(self._cover_res.value())

        # Save Files Tab
        self._settings.set_recursive_search(self._recursive_check.isChecked())
        self._settings.set_max_recent_items(self._max_recent.value())
        self._settings.set_filename_tag_pattern(self._tag_pattern.text())

        super().accept()
