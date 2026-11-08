## 2024-11-13 - PySide6 Accessible Sliders & Labels
**Learning:** PySide6 standard components like QSlider default to having an empty accessibleName, requiring explicit .setAccessibleName() for screen reader compatibility. Additionally, using inline anonymous labels in layouts prevents setting `.setBuddy()` relationships.
**Action:** Always instantiate labels as variables, assign them to variables, use an ampersand (`&`) for a keyboard accelerator, call `.setBuddy()` to map them to interactive elements, and explicitly configure accessible names for items like QSlider.
