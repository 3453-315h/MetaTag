"""About dialog for meta."""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


def _resource_path(relative: str) -> Path:
    """Resolve a resource path that works both in dev and PyInstaller bundles."""
    try:
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    except AttributeError:
        # Running from source: project root is three levels up from this file
        base = Path(__file__).parent.parent.parent
    return base / relative


class AboutDialog(QDialog):
    """About dialog — shows logo, version, and tech credits."""

    def __init__(self, version: str = "1.3.1", parent=None):
        super().__init__(parent)
        self._setup_ui(version)

    def _setup_ui(self, version: str) -> None:
        self.setWindowTitle("About MetaTag")
        self.setFixedSize(460, 480)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(32, 24, 32, 22)

        # ── Logo ──────────────────────────────────────────────────────────
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = _resource_path("img/logo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    320, 180,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                logo_label.setPixmap(scaled)
        else:
            # Fallback: styled app name text if logo file is missing
            logo_label.setText("MetaTag")
            font = logo_label.font()
            font.setPointSize(30)
            font.setBold(True)
            logo_label.setFont(font)
        layout.addWidget(logo_label)

        # ── App name + subtitle ───────────────────────────────────────────
        name_label = QLabel("MetaTag")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = name_label.font()
        font.setPointSize(22)
        font.setBold(True)
        name_label.setFont(font)
        layout.addWidget(name_label)

        sub_label = QLabel("Metadata Editor")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_font = sub_label.font()
        sub_font.setPointSize(11)
        sub_label.setFont(sub_font)
        sub_label.setObjectName("aboutSubtitle")
        layout.addWidget(sub_label)

        # ── Version ───────────────────────────────────────────────────────
        ver_label = QLabel(f"Version {version}")
        ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_font = ver_label.font()
        ver_font.setPointSize(10)
        ver_label.setFont(ver_font)
        ver_label.setObjectName("aboutVersion")
        layout.addWidget(ver_label)

        # ── GitHub Link ───────────────────────────────────────────────────
        gh_label = QLabel('<a href="https://github.com/3453-315h/MetaTag" style="color: #89b4fa; text-decoration: none;">GitHub Repository</a>')
        gh_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gh_label.setOpenExternalLinks(True)
        gh_label.setObjectName("aboutGithub")
        layout.addWidget(gh_label)

        layout.addSpacing(8)

        # ── Description ───────────────────────────────────────────────────
        desc = QLabel("Batch-edit audio file metadata with cover art support.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setObjectName("aboutDesc")
        layout.addWidget(desc)

        # ── Credits ───────────────────────────────────────────────────────
        credits = QLabel(
            "Built with: <b>Mutagen</b> · <b>PySide6</b> · <b>Pillow</b><br>"
            "Online: <b>MusicBrainz</b> · <b>Cover Art Archive</b> · <b>Discogs</b>"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setWordWrap(True)
        credits.setTextFormat(Qt.TextFormat.RichText)
        credits.setObjectName("aboutCredits")
        layout.addWidget(credits)

        layout.addSpacing(6)

        # ── OK button ─────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(100)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
