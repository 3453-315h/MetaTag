## 2025-05-18 - Qt Label-to-Input Manual Buddy Requirement
**Learning:** In PySide6, `QFormLayout.addRow()` automatically establishes buddy relationships between labels and inputs, whereas other layouts like `QHBoxLayout` require explicitly calling `label.setBuddy(widget)` to enable screen reader associations and keyboard shortcuts.
**Action:** Always manually call `setBuddy()` when laying out forms using anything other than `QFormLayout` to ensure keyboard accessibility.
