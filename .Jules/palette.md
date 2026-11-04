## 2025-02-12 - PySide6 Buddy Relationships
**Learning:** When assigning keyboard accelerators to standard labels in PySide6 layouts (like QHBoxLayout), you must explicitly use `label.setBuddy(input_widget)` and an ampersand in the text (e.g. "&Search:"). Forms like `QFormLayout.addRow()` do this automatically, but custom layout constructions do not, breaking accessibility/accelerator expectations.
**Action:** Always call `setBuddy()` explicitly when placing a QLabel adjacent to an input field in custom non-form layouts.
