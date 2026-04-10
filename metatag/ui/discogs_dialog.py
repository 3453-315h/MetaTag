"""Discogs release selection dialog."""

from typing import Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QAbstractItemView,
    QHeaderView,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal


class DiscogsDialog(QDialog):
    """Present a list of Discogs releases and let the user pick one.

    Emits ``release_selected`` with the chosen release dict when the user
    clicks *Apply*.  The caller can then populate track fields accordingly.
    """

    release_selected = Signal(dict)

    _COLUMNS = ["Artist", "Title", "Year", "Label", "Format"]

    def __init__(self, releases: list[dict[str, Any]], parent=None):
        super().__init__(parent)
        self._releases = releases
        self._setup_ui()
        self._populate(releases)

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #

    def _setup_ui(self) -> None:
        self.setWindowTitle("Discogs Search Results")
        self.resize(720, 420)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 10)

        root.addWidget(
            QLabel(f"Found <b>{len(self._releases)}</b> release(s). "
                   "Select one and click <b>Apply</b> to populate the track tags.")
        )

        # Results table
        self._table = QTableWidget(0, len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels(self._COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)

        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Artist
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)      # Title
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)        # Year
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Label
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)        # Format
        self._table.setColumnWidth(2, 60)
        self._table.setColumnWidth(4, 80)

        self._table.doubleClicked.connect(self._apply_selected)
        root.addWidget(self._table)

        # Buttons
        btn_layout = QHBoxLayout()
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setDefault(True)
        self._apply_btn.setEnabled(False)
        cancel_btn = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self._apply_btn)
        root.addLayout(btn_layout)

        self._apply_btn.clicked.connect(self._apply_selected)
        cancel_btn.clicked.connect(self.reject)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

    def _populate(self, releases: list[dict[str, Any]]) -> None:
        self._table.setRowCount(0)
        for release in releases:
            row = self._table.rowCount()
            self._table.insertRow(row)
            cells = [
                release.get("artist", ""),
                release.get("title", ""),
                str(release.get("year", "")),
                release.get("label", ""),
                release.get("format", ""),
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row, col, item)

        if releases:
            self._table.selectRow(0)

    # ------------------------------------------------------------------ #
    # Slots
    # ------------------------------------------------------------------ #

    def _on_selection_changed(self) -> None:
        self._apply_btn.setEnabled(bool(self._table.selectedItems()))

    def _apply_selected(self) -> None:
        rows = {idx.row() for idx in self._table.selectedIndexes()}
        if not rows:
            return
        row = next(iter(rows))
        if 0 <= row < len(self._releases):
            self.release_selected.emit(self._releases[row])
        self.accept()
