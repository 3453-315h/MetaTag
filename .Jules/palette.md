## 2024-03-01 - PySide6 Screen Reader Accessibility Overrides

**Learning:** Inline anonymous labels (e.g. `layout.addWidget(QLabel("Vol:"))`) prevent establishing a buddy relationship to inputs, breaking screen reader context and keyboard accelerators. Additionally, standard PySide6 components like `QSlider` lack default screen reader accessible names and require explicit `setAccessibleName()` definitions.

**Action:** Always instantiate UI elements like `QLabel` as explicit variables to assign buddy relationships via `.setBuddy()`. Add an ampersand (`&`) to the label text for keyboard accelerators. Explicitly set `.setAccessibleName()` for standard interactive components like `QSlider`.
