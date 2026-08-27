## 2026-08-27 - Adding keyboard accelerator and buddy relationship to Search Bar
**Learning:** In PySide6 applications, `QFormLayout.addRow()` automatically establishes buddy relationships, but for elements added in `QHBoxLayout` or `QVBoxLayout`, like a search bar, explicitly calling `setBuddy()` and adding an ampersand (`&`) to the label text is necessary for both screen readers and keyboard shortcuts.
**Action:** Always check `QLabel` elements that are outside of `QFormLayout` to ensure they have an associated buddy if they are intended to describe an input field.
