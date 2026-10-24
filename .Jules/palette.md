## 2024-11-20 - PySide6 Slider Accessibility
**Learning:** PySide6 default sliders (e.g., QSlider) lack an accessible name, which is necessary for screen readers. Using anonymous labels in layouts (`layout.addWidget(QLabel("Vol:"))`) prevents creating a `.setBuddy()` relationship, breaking keyboard accessibility (Alt + V accelerator).
**Action:** When working with QSliders, explicitly use `.setAccessibleName()` and instantiate descriptive labels as variables so `.setBuddy()` can link them. Add accelerators (e.g. `&Vol:`) to link keyboard shortcuts.
