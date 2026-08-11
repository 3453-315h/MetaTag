## 2024-05-24 - PySide6 Layout Accessibility
**Learning:** In PySide6, QFormLayout.addRow() automatically establishes buddy relationships between labels and inputs. For other layouts like QHBoxLayout or QVBoxLayout, we must explicitly call label.setBuddy(widget) to enable screen reader associations, and use an ampersand (&) in the label text to assign keyboard accelerators (e.g., '&Search:' for Alt+S).
**Action:** When adding form-like inputs in QHBoxLayout/QVBoxLayout in PySide6, always add an ampersand for keyboard shortcuts and call setBuddy() for screen reader support.
