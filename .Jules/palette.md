## 2024-05-24 - Accessibility for QSlider and custom label layouts
**Learning:** PySide6 standard UI elements like QSlider have an empty accessibleName by default, which means screen readers won't announce their purpose. Furthermore, outside of QFormLayout, labels need explicit `setBuddy()` to associate their keyboard accelerators (e.g. `&Vol:`) with the corresponding input widget.
**Action:** Always explicitly set `.setAccessibleName()` for standalone sliders/inputs and use `.setBuddy()` when constructing custom layouts with `QLabel`.
