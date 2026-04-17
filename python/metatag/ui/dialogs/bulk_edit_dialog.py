"""Bulk metadata editor dialog for MetaTag Pro.

Lets the user selectively fill any combination of tag fields across
all currently-selected tracks in a single, undo-able operation.
Each field has its own enable/disable checkbox — only ticked fields
are written, leaving everything else untouched.
"""

from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# (field_key, display_label, placeholder_hint, is_numeric)
_BULK_FIELDS: List[Tuple[str, str, str, bool]] = [
    ("artist",       "Artist",          "e.g. Pink Floyd",          False),
    ("album",        "Album",           "e.g. The Wall",            False),
    ("title",        "Title",           "Leave blank to keep",      False),
    ("year",         "Year",            "e.g. 1979",                True),
    ("genre",        "Genre",           "e.g. Progressive Rock",    False),
    ("composer",     "Composer",        "e.g. Roger Waters",        False),
    ("grouping",     "Grouping",        "e.g. Classic Albums",      False),
    ("bpm",          "BPM",             "e.g. 120",                 True),
    ("comment",      "Comment",         "e.g. Remastered 2011",     False),
    ("track_total",  "Track Total",     "e.g. 12",                  True),
    ("disc_number",  "Disc Number",     "e.g. 1",                   True),
    ("disc_total",   "Disc Total",      "e.g. 2",                   True),
]


class BulkEditDialog(QDialog):
    """Dialog to bulk-apply selected tag fields to N tracks.

    Usage::

        dlg = BulkEditDialog(n_tracks=5, parent=window)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fields = dlg.get_field_values()
            # fields is Dict[str, str] containing only enabled fields
    """

    def __init__(self, n_tracks: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._n_tracks = n_tracks
        self._rows: Dict[str, Tuple[QCheckBox, QLineEdit]] = {}
        self._setup_ui()
        self._connect_signals()

    # ── UI construction ───────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"Bulk Edit — {self._n_tracks} Track(s)")
        self.setMinimumWidth(520)
        self.setMaximumWidth(680)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 12, 14, 12)

        # ── Header ───────────────────────────────────────────────────────
        header = QLabel(
            f"<b>Editing {self._n_tracks} selected track(s).</b><br>"
            "<span style='color:#888;font-size:11px;'>"
            "Tick the checkbox next to each field you want to fill. "
            "Unticked fields are left unchanged.</span>"
        )
        header.setWordWrap(True)
        root.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #313244;")
        root.addWidget(sep)

        # ── Scrollable field form ─────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_w = QWidget()
        form = QFormLayout(scroll_w)
        form.setSpacing(7)
        form.setContentsMargins(4, 4, 4, 4)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for field_key, label_text, placeholder, is_numeric in _BULK_FIELDS:
            check = QCheckBox(label_text)
            check.setMinimumWidth(120)

            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setEnabled(False)          # disabled until ticked
            if is_numeric:
                edit.setMaximumWidth(120)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            row_layout.addWidget(check)
            row_layout.addWidget(edit, stretch=1)

            form.addRow(row_widget)
            self._rows[field_key] = (check, edit)

        scroll.setWidget(scroll_w)
        root.addWidget(scroll, stretch=1)

        # ── Helper buttons ────────────────────────────────────────────────
        helper_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All Fields")
        select_all_btn.clicked.connect(lambda: self._toggle_all(True))
        deselect_btn = QPushButton("Deselect All")
        deselect_btn.clicked.connect(lambda: self._toggle_all(False))
        helper_layout.addWidget(select_all_btn)
        helper_layout.addWidget(deselect_btn)
        helper_layout.addStretch()
        root.addLayout(helper_layout)

        # ── Dialog buttons ────────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #313244;")
        root.addWidget(sep2)

        btn_layout = QHBoxLayout()
        self._apply_btn = QPushButton(f"Apply to {self._n_tracks} Track(s)")
        self._apply_btn.setDefault(True)
        self._apply_btn.setEnabled(False)   # enabled when ≥1 field ticked
        self._apply_btn.setStyleSheet(
            "QPushButton { background-color: #89b4fa; color: #1e1e2e;"
            "              font-weight: bold; border-radius: 6px; padding: 6px 18px; }"
            "QPushButton:disabled { background-color: #45475a; color: #585b70; }"
            "QPushButton:hover { background-color: #b4d0fa; }"
        )
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self._apply_btn)
        root.addLayout(btn_layout)

        self._apply_btn.clicked.connect(self.accept)
        self.adjustSize()

    def _connect_signals(self) -> None:
        for field_key, (check, edit) in self._rows.items():
            check.toggled.connect(lambda checked, e=edit: e.setEnabled(checked))
            check.toggled.connect(self._refresh_apply_button)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _toggle_all(self, state: bool) -> None:
        for check, edit in self._rows.values():
            check.setChecked(state)

    def _refresh_apply_button(self) -> None:
        any_ticked = any(check.isChecked() for check, _ in self._rows.values())
        self._apply_btn.setEnabled(any_ticked)
        n = sum(1 for check, _ in self._rows.values() if check.isChecked())
        self._apply_btn.setText(
            f"Apply {n} field(s) to {self._n_tracks} track(s)" if n else
            f"Apply to {self._n_tracks} Track(s)"
        )

    # ── Public API ────────────────────────────────────────────────────────

    def get_field_values(self) -> Dict[str, str]:
        """Return a dict of {field_key: value} for every *ticked* field.

        Only fields whose checkbox is checked are included.
        The caller should skip writing fields not present in this dict.
        """
        result: Dict[str, str] = {}
        for field_key, (check, edit) in self._rows.items():
            if check.isChecked():
                result[field_key] = edit.text().strip()
        return result
