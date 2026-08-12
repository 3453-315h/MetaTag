## 2024-05-24 - Accessibility Enhancements
**Learning:** PySide6 uses `setBuddy` and keyboard accelerators (`& `) for accessible labels in layouts other than QFormLayout, improving screen reader support.
**Action:** Always verify layouts like QHBoxLayout or QVBoxLayout map labels properly to their corresponding inputs using `setBuddy` and add shortcuts with `&`.
