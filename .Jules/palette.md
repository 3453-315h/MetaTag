## 2024-05-30 - Standard UI Elements Accessible Name Defaulting
**Learning:** Standard UI elements in PySide6 like QSlider default to having an empty accessibleName. They don't automatically derive an accessible name from adjacent labels unless specifically put in a QFormLayout or explicitly associated.
**Action:** Explicitly set `.setAccessibleName()` on standalone sliders, buttons, and other interactive elements to ensure proper screen reader compatibility.
