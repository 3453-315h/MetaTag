"""Dialog for searching and selecting audiobooks via Audnexus."""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QProgressBar,
    QMessageBox,
)

from ...online.audnexus_lookup import AudiobookLookup

class AudiobookLookupDialog(QDialog):
    """Search for audiobooks and select a match."""

    def __init__(self, parent=None, initial_query: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Audiobook Lookup (Audnexus)")
        self.resize(800, 500)
        
        self._selected_data: Optional[Dict[str, Any]] = None
        self._lookup = AudiobookLookup(self)
        self._lookup.results_fetched.connect(self._on_results_fetched)
        self._lookup.details_fetched.connect(self._on_details_fetched)
        self._lookup.lookup_error.connect(self._on_error)
        
        self._setup_ui()
        
        if initial_query:
            self._search_edit.setText(initial_query)
            QTimer.singleShot(100, self._do_search)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Search area
        search_layout = QHBoxLayout()
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Enter book title or author...")
        self._search_edit.returnPressed.connect(self._do_search)
        self._search_button = QPushButton("Search")
        self._search_button.clicked.connect(self._do_search)
        
        search_layout.addWidget(self._search_edit)
        search_layout.addWidget(self._search_button)
        layout.addLayout(search_layout)
        
        # Results table
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Title", "Author", "Narrator", "Series"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.itemDoubleClicked.connect(self._fetch_and_accept)
        layout.addWidget(self._table)
        
        # Progress and Buttons
        footer_layout = QHBoxLayout()
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.hide()
        
        self._ok_button = QPushButton("Select & Apply")
        self._ok_button.setDefault(True)
        self._ok_button.setEnabled(False)
        self._cancel_button = QPushButton("Cancel")
        
        footer_layout.addWidget(self._progress)
        footer_layout.addStretch()
        footer_layout.addWidget(self._ok_button)
        footer_layout.addWidget(self._cancel_button)
        layout.addLayout(footer_layout)
        
        self._ok_button.clicked.connect(self._fetch_and_accept)
        self._cancel_button.clicked.connect(self.reject)

    @Slot()
    def _do_search(self) -> None:
        query = self._search_edit.text().strip()
        if not query:
            return
            
        self._set_loading(True)
        self._table.setRowCount(0)
        self._lookup.search_books(query)

    def _set_loading(self, loading: bool) -> None:
        self._progress.setVisible(loading)
        self._search_button.setEnabled(not loading)
        self._ok_button.setEnabled(False)

    def _on_results_fetched(self, results: List[Dict[str, Any]]) -> None:
        self._set_loading(False)
        self._results = results
        self._table.setRowCount(0)
        
        for res in results:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(res.get("title", "")))
            self._table.setItem(row, 1, QTableWidgetItem(res.get("artist", "")))
            self._table.setItem(row, 2, QTableWidgetItem(res.get("narrator", "")))
            self._table.setItem(row, 3, QTableWidgetItem(res.get("series", "")))
            
        if results:
            self._table.selectRow(0)
            self._ok_button.setEnabled(True)
        else:
            QMessageBox.information(self, "No Results", "No matching audiobooks found.")

    def _fetch_and_accept(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return

        asin = self._results[row].get("id")
        if not asin:
            QMessageBox.warning(self, "Error", "Selected book has no ASIN identifier.")
            return
        # Show loading state while fetching full details
        self._set_loading(True)
        self._lookup.fetch_book_details(asin)

    def _on_details_fetched(self, details: Dict[str, Any]) -> None:
        self._selected_data = details
        self.accept()

    def _on_error(self, message: str) -> None:
        self._set_loading(False)
        QMessageBox.critical(self, "Lookup Error", message)

    def get_selected_book(self) -> Optional[Dict[str, Any]]:
        """Return the full metadata for the selected book."""
        return self._selected_data
