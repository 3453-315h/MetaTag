## 2026-08-05 - Keyboard Accessibility and Buddy Relations
**Learning:** In PySide6, UI elements added to layouts like QHBoxLayout don't automatically associate labels with inputs for screen readers and keyboard navigation (unlike QFormLayout). It's necessary to explicitly use `label.setBuddy(widget)` and add an ampersand (&) to the label text to assign a keyboard accelerator.
**Action:** Always check for standalone labels next to input widgets or sliders and establish buddy relations to improve keyboard navigation.
