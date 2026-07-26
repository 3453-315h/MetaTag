"""Dialog for regex find & replace."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal


class RegexDialog(QDialog):
    """Dialog to input regex find/replace pattern."""

    pattern_accepted = Signal(
        str, str, list, bool
    )  # pattern, replacement, fields, case_sensitive

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pattern = ""
        self._replacement = ""
        self._selected_fields = []
        self._case_sensitive = True
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Find & Replace")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Pattern
        layout.addWidget(QLabel("Find (regular expression):"))
        self._pattern_edit = QLineEdit()
        self._pattern_edit.setPlaceholderText(r"\d{4}")
        layout.addWidget(self._pattern_edit)

        layout.addWidget(QLabel("Replace with:"))
        self._replacement_edit = QLineEdit()
        self._replacement_edit.setPlaceholderText("YYYY")
        layout.addWidget(self._replacement_edit)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        self._case_check = QCheckBox("Case sensitive")
        self._case_check.setChecked(True)
        options_layout.addWidget(self._case_check)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Fields to apply
        fields_group = QGroupBox("Apply to fields")
        fields_layout = QVBoxLayout()
        self._field_list = QListWidget()
        self._field_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        fields = [
            ("Artist", "artist"),
            ("Album", "album"),
            ("Title", "title"),
            ("Genre", "genre"),
            ("Comment", "comment"),
            ("Composer", "composer"),
            ("Grouping", "grouping"),
        ]
        for label, key in fields:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._field_list.addItem(item)
        fields_layout.addWidget(self._field_list)
        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)

        # Buttons
        button_layout = QHBoxLayout()
        self._ok_button = QPushButton("OK")
        self._cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self._ok_button)
        button_layout.addWidget(self._cancel_button)
        layout.addLayout(button_layout)

        # Connections
        self._ok_button.clicked.connect(self._accept)
        self._cancel_button.clicked.connect(self.reject)

    def _accept(self):
        pattern = self._pattern_edit.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Pattern Empty", "Please enter a pattern.")
            return
        replacement = self._replacement_edit.text()
        selected_fields = []
        for item in self._field_list.selectedItems():
            selected_fields.append(item.data(Qt.ItemDataRole.UserRole))
        if not selected_fields:
            QMessageBox.warning(self, "No Fields", "Please select at least one field.")
            return
        self._pattern = pattern
        self._replacement = replacement
        self._selected_fields = selected_fields
        self._case_sensitive = self._case_check.isChecked()
        self.pattern_accepted.emit(
            pattern, replacement, selected_fields, self._case_sensitive
        )
        super().accept()

    def pattern(self) -> str:
        return self._pattern

    def replacement(self) -> str:
        return self._replacement

    def selected_fields(self) -> list[str]:
        return self._selected_fields

    def case_sensitive(self) -> bool:
        return self._case_sensitive
