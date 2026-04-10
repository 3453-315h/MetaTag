"""Table model for MetaTag."""

from typing import List, Optional, Any
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from ...core.track import Track

class TrackModel(QAbstractTableModel):
    """Data model mapping Track objects to table rows."""

    _COLUMN_NUM    = 0
    _COLUMN_TITLE  = 1
    _COLUMN_ARTIST = 2
    _COLUMN_ALBUM  = 3
    _COLUMN_DUR    = 4
    _HEADERS = ["#", "Title", "Artist", "Album", "Duration"]

    def __init__(self, tracks: List[Track], parent=None):
        super().__init__(parent)
        self._tracks = tracks

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._tracks)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        track = self._tracks[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == self._COLUMN_NUM:
                return str(track.track_number) if track.track_number > 0 else ""
            if col == self._COLUMN_TITLE:
                return track.title
            if col == self._COLUMN_ARTIST:
                return track.artist
            if col == self._COLUMN_ALBUM:
                return track.album
            if col == self._COLUMN_DUR:
                # Format duration (seconds -> MM:SS)
                d = track.duration
                return f"{int(d // 60)}:{int(d % 60):02d}" if d > 0 else ""

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in (self._COLUMN_NUM, self._COLUMN_DUR):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        # For custom tooltips or internal mapping
        if role == Qt.ItemDataRole.UserRole:
            return track

        return None

    def refresh(self) -> None:
        """Force a total refresh of the view."""
        self.layoutChanged.emit()

    def update_row(self, row: int) -> None:
        """Refresh a single row's metadata display."""
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
