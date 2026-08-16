## 2024-05-18 - Explicit Buddy Assignments in PySide6 Layouts
**Learning:** In PySide6, while `QFormLayout` automatically establishes buddy relationships between labels and inputs, other layouts like `QHBoxLayout` or `QVBoxLayout` do not. Missing this explicit association breaks screen reader navigation for forms constructed manually outside of a `QFormLayout`.
**Action:** When creating forms using raw layouts (like horizontal or vertical boxes) in PySide6/Qt, always explicitly call `label.setBuddy(input_widget)` and use an ampersand (`&`) in the label text to assign a keyboard accelerator.
