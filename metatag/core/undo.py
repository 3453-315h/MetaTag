"""Undo/Redo commands for MetaTag."""

from typing import Any, List, Optional
from PySide6.QtGui import QUndoCommand
from PIL import Image

class TagEditCommand(QUndoCommand):
    """Command to change a metadata field for one or more tracks."""

    def __init__(self, window: Any, track_indices: List[int], field: str, new_value: str, description: str = ""):
        super().__init__(description or f"Edit {field}")
        self._window = window
        self._indices = track_indices
        self._field = field
        self._new_value = new_value
        
        # Capture old values
        self._old_values = []
        for idx in track_indices:
            track = window._tracks[idx]
            self._old_values.append(getattr(track, field))

    def redo(self) -> None:
        self._apply(self._new_value)

    def undo(self) -> None:
        # Note: self._old_values is a list, but for simplicity in this 
        # multi-track command, we apply them individually.
        for idx, old_val in zip(self._indices, self._old_values):
            self._apply(old_val, single_idx=idx)

    def _apply(self, value: Any, single_idx: Optional[int] = None) -> None:
        target_indices = [single_idx] if single_idx is not None else self._indices
        
        for idx in target_indices:
            track = self._window._tracks[idx]
            
            # Special handling for numeric fields (reuse logic from main_window)
            _numeric = ("year", "bpm", "track_number", "disc_number", "track_total", "disc_total")
            if self._field in _numeric:
                try:
                    setattr(track, self._field, int(str(value).strip()) if str(value).strip() else 0)
                except ValueError:
                    pass
            else:
                setattr(track, self._field, str(value))
                
            # Notify the model that data changed for this row
            self._window._track_model.update_row(idx)
        
        # If the currently viewed track was modified, refresh the editor fields
        if self._window._current_index in target_indices:
            self._window._load_track(self._window._current_index)


class CoverChangeCommand(QUndoCommand):
    """Command to change the cover art for one or more tracks."""

    def __init__(self, tracks: List[Any], new_image: Optional[Image.Image], description: str = "Change Cover Art"):
        super().__init__(description)
        self._tracks = tracks
        self._new_image = new_image
        self._old_images = [t.cover_art for t in tracks]

    def redo(self) -> None:
        for track in self._tracks:
            track.cover_art = self._new_image

    def undo(self) -> None:
        for track, img in zip(self._tracks, self._old_images):
            track.cover_art = img
