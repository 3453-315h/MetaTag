"""Dialog for selecting a release from search results."""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
)

class PickReleaseDialog(QDialog):
    """Dialog to pick a release from online search results."""

    def __init__(self, parent=None, results: List[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Select Release")
        self.resize(700, 400)
        self._results = results or []
        self._selected_id: Optional[str] = None
        
        self._setup_ui()
        self._populate_table()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Multiple matches found. Please select the correct release:"))
        
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Album Title", "Artist", "Year", "Label"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.itemDoubleClicked.connect(lambda _: self.accept())
        layout.addWidget(self._table)
        
        btn_layout = QHBoxLayout()
        self._ok_button = QPushButton("Select")
        self._ok_button.setDefault(True)
        self._cancel_button = QPushButton("Cancel")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self._ok_button)
        btn_layout.addWidget(self._cancel_button)
        layout.addLayout(btn_layout)
        
        self._ok_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)

    def _populate_table(self) -> None:
        self._table.setRowCount(0)
        for res in self._results:
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            self._table.setItem(row, 0, QTableWidgetItem(res.get("title", "Unknown")))
            self._table.setItem(row, 1, QTableWidgetItem(res.get("artist", "Unknown")))
            self._table.setItem(row, 2, QTableWidgetItem(str(res.get("year", ""))))
            self._table.setItem(row, 3, QTableWidgetItem(res.get("label", "")))

    def selected_release_id(self) -> Optional[str]:
        """Return the ID of the selected release."""
        row = self._table.currentRow()
        if 0 <= row < len(self._results):
            return self._results[row].get("id")
        return None
