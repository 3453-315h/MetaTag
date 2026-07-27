## 2024-05-18 - Explicit label associations in Qt layouts
**Learning:** In PySide6, QFormLayout.addRow() automatically establishes buddy relationships between labels and inputs, whereas other layouts like QHBoxLayout require explicitly calling `label.setBuddy(widget)` to enable screen reader associations and keyboard shortcuts.
**Action:** Always call `label.setBuddy(widget)` when placing a descriptive QLabel adjacent to an input widget in non-QFormLayout containers.
