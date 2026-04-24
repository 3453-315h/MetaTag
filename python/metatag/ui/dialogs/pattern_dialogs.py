"""Automation dialogs for MetaTag Pro."""

from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from ...utils.patterns import parse_filename, format_filename, PLACEHOLDERS

class PatternDialogBase(QDialog):
    """Base class for pattern-based automation dialogs."""
    
    def __init__(self, parent=None, title="", pattern_placeholder=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 500)
        
        self._setup_ui(pattern_placeholder)
        
    def _setup_ui(self, placeholder: str) -> None:
        layout = QVBoxLayout(self)
        
        # Pattern input
        p_layout = QHBoxLayout()
        p_layout.addWidget(QLabel("Pattern:"))
        self._pattern_edit = QLineEdit()
        self._pattern_edit.setPlaceholderText(placeholder)
        p_layout.addWidget(self._pattern_edit)
        layout.addLayout(p_layout)
        
        # Shortcuts / Help
        help_label = QLabel(f"Available tags: {', '.join(PLACEHOLDERS.keys())}")
        help_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(help_label)
        
        # Preview Table
        self._preview_table = QTableWidget(0, 2)
        self._preview_table.setHorizontalHeaderLabels(["Original", "Previewed Change"])
        self._preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._preview_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self._apply_button = QPushButton("Apply to Selected")
        self._apply_button.setDefault(True)
        self._cancel_button = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(self._apply_button)
        btn_layout.addWidget(self._cancel_button)
        layout.addLayout(btn_layout)
        
        self._apply_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)
        self._pattern_edit.textChanged.connect(self._on_pattern_changed)

    def _on_pattern_changed(self, text: str) -> None:
        """Abstract method to update the preview table."""
        pass

    def pattern(self) -> str:
        return self._pattern_edit.text().strip()

    def set_pattern(self, pattern: str) -> None:
        self._pattern_edit.setText(pattern)
        self._on_pattern_changed(pattern)


class TagFromFilenameDialog(PatternDialogBase):
    """Dialog for extracting tags from file names."""
    
    def __init__(self, parent=None, tracks: List[Any] = None, default_pattern: str = ""):
        super().__init__(parent, "Tag from Filename", default_pattern or "%artist% - %title%")
        self._tracks = tracks or []
        if default_pattern:
            self.set_pattern(default_pattern)
        else:
            self._update_preview()
        
    def _on_pattern_changed(self, text: str) -> None:
        self._update_preview()

    def _update_preview(self) -> None:
        pattern = self.pattern()
        self._preview_table.setRowCount(0)
        if not pattern:
            return
            
        for i, track in enumerate(self._tracks):
            filename = track.file_path.stem
            tags = parse_filename(filename, pattern)
            
            row = self._preview_table.rowCount()
            self._preview_table.insertRow(row)
            self._preview_table.setItem(row, 0, QTableWidgetItem(filename))
            
            if tags:
                tag_str = ", ".join(f"{k}: {v}" for k, v in tags.items())
                item = QTableWidgetItem(tag_str)
                item.setForeground(Qt.GlobalColor.green)
            else:
                item = QTableWidgetItem("No match")
                item.setForeground(Qt.GlobalColor.red)
            
            self._preview_table.setItem(row, 1, item)


class BatchRenameDialog(PatternDialogBase):
    """Dialog for renaming files based on tags."""
    
    def __init__(self, parent=None, tracks: List[Any] = None, default_pattern: str = ""):
        super().__init__(parent, "Batch Rename from Tags", default_pattern or "%track% - %title%")
        self._tracks = tracks or []
        if default_pattern:
            self.set_pattern(default_pattern)
        else:
            self._update_preview()

    def _on_pattern_changed(self, text: str) -> None:
        self._update_preview()

    def _update_preview(self) -> None:
        pattern = self.pattern()
        self._preview_table.setRowCount(0)
        if not pattern:
            return

        for i, track in enumerate(self._tracks):
            old_name = track.file_path.name
            
            # Map track attributes to a dict for format_filename
            tags = {
                "artist": track.artist,
                "album": track.album,
                "title": track.title,
                "track_number": track.track_number,
                "disc_number": track.disc_number,
                "year": track.year,
            }
            new_name = format_filename(tags, pattern) + track.file_path.suffix
            
            row = self._preview_table.rowCount()
            self._preview_table.insertRow(row)
            self._preview_table.setItem(row, 0, QTableWidgetItem(old_name))
            
            item = QTableWidgetItem(new_name)
            if new_name != old_name:
                item.setForeground(Qt.GlobalColor.cyan)
            self._preview_table.setItem(row, 1, item)
