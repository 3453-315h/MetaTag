"""Undo/Redo commands for MetaTag."""

from typing import Any, List, Optional, Union
from PySide6.QtGui import QUndoCommand
from PIL import Image

class TagEditCommand(QUndoCommand):
    """Command to change a metadata field for one or more tracks with stable track identity."""

    def __init__(
        self,
        window: Any,
        targets: Union[List[int], List[Any]],
        field: str,
        new_value: Any,
        description: str = "",
    ):
        super().__init__(description or f"Edit {field}")
        self._window = window
        self._field = field
        self._new_value = new_value
        self._session_id = getattr(window, "_session_id", 0)

        # Resolve targets to stable Track objects
        self._tracks = []
        for item in targets:
            if isinstance(item, int):
                if 0 <= item < len(window._tracks):
                    self._tracks.append(window._tracks[item])
            else:
                self._tracks.append(item)

        # Capture old values using stable identity
        self._old_values = [getattr(track, field) for track in self._tracks]
        self._is_first_redo = True

    def redo(self) -> None:
        if getattr(self._window, "_session_id", 0) != self._session_id:
            return
        self._apply(self._new_value, is_undo_redo=not self._is_first_redo)
        self._is_first_redo = False

    def undo(self) -> None:
        if getattr(self._window, "_session_id", 0) != self._session_id:
            return
        for track, old_val in zip(self._tracks, self._old_values):
            self._apply(old_val, single_track=track, is_undo_redo=True)

    def _apply(
        self,
        value: Any,
        single_track: Optional[Any] = None,
        is_undo_redo: bool = False,
    ) -> None:
        target_tracks = [single_track] if single_track is not None else self._tracks
        _numeric = ("year", "bpm", "track_number", "disc_number", "track_total", "disc_total")

        for track in target_tracks:
            # Check stable identity against current session
            if track not in self._window._tracks:
                # Track was removed from session — do not affect remaining tracks or crash
                continue

            row = self._window._tracks.index(track)

            if self._field in _numeric:
                try:
                    val_str = str(value).strip() if value is not None else ""
                    setattr(track, self._field, int(val_str) if val_str else 0)
                except ValueError:
                    pass
            else:
                setattr(track, self._field, str(value) if value is not None else "")

            track.is_dirty = True
            # Notify the model that data changed for this row
            self._window._track_model.update_row(row)

        if is_undo_redo and 0 <= self._window._current_index < len(self._window._tracks):
            current_track = self._window._tracks[self._window._current_index]
            if current_track in target_tracks:
                self._window._load_track(self._window._current_index)


class CoverChangeCommand(QUndoCommand):
    """Command to change the cover art for one or more tracks with stable track identity."""

    def __init__(
        self,
        window: Any,
        tracks: Union[List[int], List[Any]],
        new_image: Optional[Image.Image],
        description: str = "Change Cover Art",
    ):
        super().__init__(description)
        self._window = window
        self._session_id = getattr(window, "_session_id", 0)
        self._tracks = []
        for t in tracks:
            if isinstance(t, int):
                if 0 <= t < len(window._tracks):
                    self._tracks.append(window._tracks[t])
            else:
                self._tracks.append(t)

        self._new_image = new_image
        self._old_images = [t.cover_art for t in self._tracks]
        self._is_first_redo = True

    def redo(self) -> None:
        if getattr(self._window, "_session_id", 0) != self._session_id:
            return
        is_undo_redo = not self._is_first_redo
        for track in self._tracks:
            if track in self._window._tracks:
                track.cover_art = self._new_image
                track.is_dirty = True
                row = self._window._tracks.index(track)
                if hasattr(self._window, "_track_model"):
                    self._window._track_model.update_row(row)

        if is_undo_redo:
            self._update_ui()
        self._is_first_redo = False

    def undo(self) -> None:
        if getattr(self._window, "_session_id", 0) != self._session_id:
            return
        for track, img in zip(self._tracks, self._old_images):
            if track in self._window._tracks:
                track.cover_art = img
                track.is_dirty = True
                row = self._window._tracks.index(track)
                if hasattr(self._window, "_track_model"):
                    self._window._track_model.update_row(row)
        self._update_ui()

    def _update_ui(self) -> None:
        if getattr(self._window, "_session_id", 0) != self._session_id:
            return
        if 0 <= self._window._current_index < len(self._window._tracks):
            current_track = self._window._tracks[self._window._current_index]
            if current_track in self._tracks:
                self._window._cover_label.setCoverImage(current_track.cover_art, current_track.album)
