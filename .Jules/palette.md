
## 2024-05-18 - QSlider accessibility support
**Learning:** Standard UI elements like `QSlider` in PySide6/Qt default to having an empty `accessibleName`, meaning screen readers cannot announce them properly without explicitly setting it.
**Action:** Always ensure that an `accessibleName` is set for `QSlider` widgets and check other seemingly obvious interactive UI elements in PySide6 to ensure proper screen reader compatibility.
