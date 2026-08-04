## 2024-08-04 - PySide6 Layout Accessibility
**Learning:** In PySide6, while `QFormLayout.addRow()` automatically establishes buddy relationships between labels and inputs for screen readers, other layouts like `QHBoxLayout` or `QVBoxLayout` do not.
**Action:** Explicitly call `label.setBuddy(widget)` when using non-form layouts to enable screen reader associations, and use an ampersand (`&`) in the label text to assign keyboard accelerators (e.g., `'&Search:'` for Alt+S).
