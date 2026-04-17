"""Application configuration."""

from pathlib import Path
from PySide6.QtCore import QSettings
from typing import List

# Field keys corresponding to Track attributes and UI labels
FIELD_KEYS = [
    "artist",
    "album",
    "title",
    "track_number",
    "year",
    "genre",
    "disc_number",
    "comment",
    "composer",
    "grouping",
    "bpm",
]

DEFAULT_VISIBLE_FIELDS = FIELD_KEYS.copy()
DEFAULT_FIELD_ORDER    = FIELD_KEYS.copy()
_MAX_RECENT = 5


def get_version() -> str:
    """Return the application version string."""
    try:
        from importlib.metadata import version
        return version("MetaTag")
    except Exception:
        pass
    try:
        import tomllib
        toml_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if toml_path.exists():
            with toml_path.open("rb") as f:
                data = tomllib.load(f)
            return data["project"].get("version", "1.3.0")
    except Exception:
        pass
    return "1.3.0"


class Settings:
    """Application settings using QSettings."""

    def __init__(self, organization: str = "MetaTag", application: str = "MetaTag"):
        self._settings = QSettings(organization, application)

    # ── Visibility ────────────────────────────────────────────────────────

    def visible_fields(self) -> List[str]:
        visible = self._settings.value("ui/visible_fields")
        if visible is None:
            return DEFAULT_VISIBLE_FIELDS
        return list(visible)

    def set_visible_fields(self, fields: List[str]) -> None:
        valid = [f for f in fields if f in FIELD_KEYS]
        seen: set[str] = set()
        unique = [f for f in valid if not (f in seen or seen.add(f))]  # type: ignore[func-returns-value]
        self._settings.setValue("ui/visible_fields", unique)

    # ── Ordering (FIX #21) ────────────────────────────────────────────────

    def field_order(self) -> List[str]:
        stored = self._settings.value("ui/field_order")
        if stored is None:
            return DEFAULT_FIELD_ORDER.copy()
        order = list(stored)
        for key in FIELD_KEYS:
            if key not in order:
                order.append(key)
        return order

    def set_field_order(self, order: List[str]) -> None:
        valid = [f for f in order if f in FIELD_KEYS]
        for key in FIELD_KEYS:
            if key not in valid:
                valid.append(key)
        self._settings.setValue("ui/field_order", valid)

    # ── Recent Folders ────────────────────────────────────────────────────

    def recent_folders(self) -> List[str]:
        """Return the last ≤5 opened folder paths (most recent first)."""
        stored = self._settings.value("ui/recent_folders")
        if stored is None:
            return []
        return list(stored)

    def add_recent_folder(self, folder: str) -> None:
        """Prepend *folder* to the recent list, capping at _MAX_RECENT entries."""
        folders = self.recent_folders()
        if folder in folders:
            folders.remove(folder)
        folders.insert(0, folder)
        self._settings.setValue("ui/recent_folders", folders[:_MAX_RECENT])

    def clear_recent_folders(self) -> None:
        self._settings.remove("ui/recent_folders")

    def max_recent_items(self) -> int:
        val = self._settings.value("ui/max_recent_items")
        return int(val) if val is not None else _MAX_RECENT

    def set_max_recent_items(self, count: int) -> None:
        self._settings.setValue("ui/max_recent_items", count)

    # ── General Logic ─────────────────────────────────────────────────────

    def auto_save_enabled(self) -> bool:
        val = self._settings.value("ui/auto_save_enabled")
        return bool(int(val)) if val is not None else True

    def set_auto_save_enabled(self, enabled: bool) -> None:
        self._settings.setValue("ui/auto_save_enabled", int(enabled))

    def auto_save_interval(self) -> int:
        val = self._settings.value("ui/auto_save_interval")
        return int(val) if val is not None else 800

    def set_auto_save_interval(self, ms: int) -> None:
        self._settings.setValue("ui/auto_save_interval", ms)

    def preserve_timestamps(self) -> bool:
        val = self._settings.value("core/preserve_timestamps")
        return bool(int(val)) if val is not None else False

    def set_preserve_timestamps(self, enabled: bool) -> None:
        self._settings.setValue("core/preserve_timestamps", int(enabled))

    def restore_last_dir(self) -> bool:
        val = self._settings.value("core/restore_last_dir")
        return bool(int(val)) if val is not None else True

    def set_restore_last_dir(self, enabled: bool) -> None:
        self._settings.setValue("core/restore_last_dir", int(enabled))

    def recursive_search(self) -> bool:
        val = self._settings.value("core/recursive_search")
        return bool(int(val)) if val is not None else True

    def set_recursive_search(self, enabled: bool) -> None:
        self._settings.setValue("core/recursive_search", int(enabled))

    def filename_tag_pattern(self) -> str:
        val = self._settings.value("core/filename_tag_pattern")
        return str(val) if val else "%artist% - %title%"

    def set_filename_tag_pattern(self, pattern: str) -> None:
        self._settings.setValue("core/filename_tag_pattern", pattern.strip())

    # ── Online ────────────────────────────────────────────────────────────

    def discogs_token(self) -> str:
        return str(self._settings.value("online/discogs_token", ""))

    def set_discogs_token(self, token: str) -> None:
        self._settings.setValue("online/discogs_token", token.strip())

    def musicbrainz_url(self) -> str:
        return str(self._settings.value("online/musicbrainz_url", "https://musicbrainz.org"))

    def set_musicbrainz_url(self, url: str) -> None:
        self._settings.setValue("online/musicbrainz_url", url.strip())

    def cover_max_res(self) -> int:
        val = self._settings.value("online/cover_max_res")
        return int(val) if val is not None else 800

    def set_cover_max_res(self, res: int) -> None:
        self._settings.setValue("online/cover_max_res", res)

    # ── Reset ─────────────────────────────────────────────────────────────

    def reset_to_defaults(self) -> None:
        """Reset all UI settings to factory defaults."""
        for key in self._settings.allKeys():
            self._settings.remove(key)
