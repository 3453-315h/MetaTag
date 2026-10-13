## 2024-10-14 - Accessible PySide6 QSliders
**Learning:** In PySide6, standard UI elements like QSlider default to having an empty accessibleName, preventing proper screen reader interaction. Also, anonymous inline labels prevent setting buddy relationships.
**Action:** Explicitly set .setAccessibleName() on QSliders. Avoid anonymous inline labels; instantiate them to explicitly bind them via .setBuddy() with a keyboard accelerator (&).
