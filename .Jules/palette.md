## 2024-05-15 - Missing Accessible Names on Standard Qt Sliders
**Learning:** In PySide6, standard UI elements like `QSlider` lack default accessible names. Relying solely on adjacent labels without `setBuddy()` or missing `setAccessibleName()` means screen reader users receive no context when navigating to the slider.
**Action:** Always explicitly set `setAccessibleName()` on `QSlider` (and similar standard input widgets) and ensure that when labels are placed in a `QHBoxLayout` or `QVBoxLayout`, they explicitly call `label.setBuddy(widget)` rather than assuming an implicit association.
