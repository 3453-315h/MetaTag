## 2024-05-24 - PySide6 Audio Player Accessibility
**Learning:** In PySide6, `QSlider` widgets default to having an empty `accessibleName`, which makes them unusable for screen readers. Furthermore, using anonymous inline labels like `layout.addWidget(QLabel("Vol:"))` prevents setting up proper buddy relationships (`.setBuddy()`) and keyboard accelerators (`&`).
**Action:** Always instantiate labels as variables (e.g., `self._vol_label = QLabel("&Vol:")`), use `.setBuddy()` to link them to their inputs, and explicitly set `.setAccessibleName()` on sliders.
