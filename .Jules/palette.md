## 2023-10-03 - Added Accessible Names to QSliders
**Learning:** In PySide6, standard UI elements like QSlider default to having an empty accessibleName, which means screen readers do not announce their purpose.
**Action:** Explicitly set `.setAccessibleName()` on QSliders and similar standard widgets to ensure screen reader compatibility.
