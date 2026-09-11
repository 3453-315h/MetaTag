## 2024-05-13 - [Init]
**Learning:** Initializing palette journal.
**Action:** None.

## 2024-05-13 - [QHBoxLayout Label Buddy Accessibility]
**Learning:** In PySide6, unlike `QFormLayout` which handles it automatically, standard layouts like `QHBoxLayout` require explicitly calling `setBuddy()` to link a label to its input field for screen reader associations and keyboard shortcuts (e.g. `&Search:` for Alt+S).
**Action:** Always verify if non-form layouts explicitly use `setBuddy()` for labeled interactive elements.
