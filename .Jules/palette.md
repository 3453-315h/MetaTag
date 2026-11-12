## 2024-05-24 - PySide6 Layout Buddy Association
**Learning:** In PySide6, `QFormLayout.addRow()` automatically establishes buddy relationships between labels and inputs, but for other layouts like `QHBoxLayout` or `QVBoxLayout`, you must explicitly call `label.setBuddy(widget)` to enable screen reader associations, and use an ampersand (&) in the label text to assign keyboard accelerators.
**Action:** Always explicitly set buddies for labels and add keyboard accelerators in custom layouts to ensure full accessibility and keyboard navigation.
