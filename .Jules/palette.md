## 2026-09-07 - PySide6 Label Accessibility
**Learning:** In PySide6, labels created outside of QFormLayout do not automatically associate with their input fields. Without a buddy association, screen readers cannot properly contextualize the input, and keyboard users cannot easily navigate to it. Furthermore, a simple ampersand (&) in the label text can serve as an effective keyboard accelerator.
**Action:** When adding labels (e.g. for a search bar in a QHBoxLayout), explicitly call `label.setBuddy(widget)` and add an ampersand (`&`) to the label text to assign an accelerator.
