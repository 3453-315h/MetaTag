## 2026-08-18 - Layout Buddy Relationships in PySide6
**Learning:** In PySide6, QFormLayout automatically associates labels with their input fields for screen readers. However, when using other layouts like QHBoxLayout or QVBoxLayout, this relationship is lost, breaking accessibility.
**Action:** Always explicitly call `label.setBuddy(input_widget)` when pairing labels and inputs outside of a QFormLayout to ensure proper screen reader support and keyboard shortcuts.
