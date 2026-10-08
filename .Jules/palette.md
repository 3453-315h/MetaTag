## 2025-02-23 - Accessibility of Standalone Labels in PySide6

**Learning:** When using standard UI elements in layouts like QHBoxLayout or QVBoxLayout in PySide6 (e.g., outside of QFormLayout which automatically manages buddy associations), labels do not automatically associate with their corresponding input fields for screen readers, and standard UI elements like QLineEdit may default to having an empty accessibleName. Also, using inline anonymous labels prevents setting `.setBuddy()` relationships, meaning they must be explicitly instantiated as variables.

**Action:** Always explicitly instantiate labels as variables when outside of QFormLayout, call `label.setBuddy(widget)` to establish a screen reader association, use an ampersand (`&`) in the label text to assign keyboard accelerators, and explicitly call `widget.setAccessibleName("...")` to provide a proper name for assistive technologies.
