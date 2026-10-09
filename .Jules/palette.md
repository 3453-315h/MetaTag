## 2024-05-24 - Accessible PySide6 Sliders
**Learning:** PySide6 default sliders (like `QSlider`) have empty accessible names by default, and using inline anonymous labels (e.g., `layout.addWidget(QLabel('Vol:'))`) prevents establishing a buddy relationship for screen readers.
**Action:** Always instantiate labels as variables, assign them keyboard accelerators (using `&`), use `.setBuddy()` to link them to their target widget, and ensure sliders have explicitly set accessible names using `.setAccessibleName()`.
