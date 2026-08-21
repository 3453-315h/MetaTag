## 2024-05-18 - PySide6 Layout Buddy Relationships
**Learning:** While `QFormLayout.addRow()` automatically establishes screen reader buddy relationships between labels and inputs, manual layouts like `QHBoxLayout` do not. Missing this breaks keyboard accelerators and screen reader context for search bars.
**Action:** Always explicitly call `label.setBuddy(input)` and add an ampersand (`&`) to the label text when manually pairing labels and inputs in non-form layouts.
