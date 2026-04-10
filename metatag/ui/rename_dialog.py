"""Dialog for pattern‑based file renaming."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal


class RenameDialog(QDialog):
    """Dialog to input a renaming pattern."""

    pattern_accepted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pattern = ""
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Rename Files")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Explanation
        layout.addWidget(
            QLabel(
                "Enter a pattern using placeholders:\n"
                "%artist%, %album%, %title%, %track%, %track2% (2 digits), %track3% (3 digits), "
                "%disc%, %genre%, %year%, %comment%, %composer%, %grouping%, %bpm%, "
                "%filename% (original name), %ext% (extension)."
            )
        )

        # Pattern entry
        self._pattern_edit = QLineEdit()
        self._pattern_edit.setPlaceholderText("%artist% - %title%")
        layout.addWidget(QLabel("Pattern:"))
        layout.addWidget(self._pattern_edit)

        # Preview label (optional)
        self._preview_label = QLabel()
        self._preview_label.setWordWrap(True)
        layout.addWidget(self._preview_label)

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
        self._pattern_edit.textChanged.connect(self._update_preview)

    def _update_preview(self, text):
        """Update preview label with example."""
        # Simple example using dummy data
        example = text.replace("%artist%", "Artist")
        example = example.replace("%album%", "Album")
        example = example.replace("%title%", "Title")
        example = example.replace("%track%", "01")
        example = example.replace("%track2%", "01")
        example = example.replace("%track3%", "001")
        example = example.replace("%disc%", "1")
        example = example.replace("%genre%", "Rock")
        example = example.replace("%year%", "2023")
        example = example.replace("%comment%", "Comment")
        example = example.replace("%composer%", "Composer")
        example = example.replace("%grouping%", "Group")
        example = example.replace("%bpm%", "120")
        example = example.replace("%filename%", "oldname")
        example = example.replace("%ext%", "mp3")
        self._preview_label.setText(f"Example: {example}")

    def _accept(self):
        pattern = self._pattern_edit.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Pattern Empty", "Please enter a pattern.")
            return
        self._pattern = pattern
        self.pattern_accepted.emit(pattern)
        super().accept()

    def pattern(self) -> str:
        """Return the entered pattern."""
        return self._pattern
