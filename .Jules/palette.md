## 2024-05-24 - Explicit setBuddy in PySide6 QHBoxLayout
**Learning:** In PySide6, while `QFormLayout.addRow()` automatically establishes buddy relationships between labels and inputs (which connects screen readers and keyboard shortcuts), other layouts like `QHBoxLayout` do not. You must explicitly call `label.setBuddy(widget)` to enable screen reader associations and keyboard shortcuts.
**Action:** Always manually call `setBuddy` when adding labeled inputs to a `QHBoxLayout` or `QVBoxLayout` in PySide6.
