## 2024-09-06 - Explicit Buddy Associations in PySide6 Layouts
**Learning:** In PySide6, while `QFormLayout.addRow()` automatically establishes buddy relationships between labels and input fields for screen readers, other layouts like `QHBoxLayout` or `QVBoxLayout` do not. Missing these explicit links impairs accessibility.
**Action:** When creating custom layouts, always manually associate labels with their corresponding inputs using `label.setBuddy(widget)` and add keyboard accelerators (e.g., `&Search:`) to the label text.
