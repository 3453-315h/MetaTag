## 2024-07-26 - PySide6 Screen Reader Accessibility
**Learning:** In PySide6 applications, `QFormLayout.addRow()` automatically creates screen reader associations between labels and inputs. However, for custom layouts like `QHBoxLayout` or `QVBoxLayout`, standard web-based HTML/ARIA attributes do not work. Accessibility and keyboard shortcuts must be explicitly defined.
**Action:** Always use `label.setBuddy(widget)` and include `&` in the label text to enable keyboard navigation and proper screen reader context for non-form layouts in PySide6.
