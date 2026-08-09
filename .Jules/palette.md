## 2026-08-09 - Keyboard Accessibility in Layouts
**Learning:** In PySide6, QFormLayout.addRow() handles label/input associations automatically. However, for manual layouts like QHBoxLayout, screen readers lose context, and keyboard shortcuts require explicit  associations.
**Action:** Always link a QLabel to its associated widget using `.setBuddy(widget)` and assign an accelerator using `&` when placing them together in non-form layouts.
## 2026-08-09 - Keyboard Accessibility in Layouts
**Learning:** In PySide6, QFormLayout.addRow() handles label/input associations automatically. However, for manual layouts like QHBoxLayout, screen readers lose context, and keyboard shortcuts require explicit .setBuddy() associations.
**Action:** Always link a QLabel to its associated widget using .setBuddy(widget) and assign an accelerator using & when placing them together in non-form layouts.
