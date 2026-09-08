## 2024-05-24 - Qt Sliders Lack Default Accessible Names
**Learning:** Standard Qt slider components like `QSlider` do not have default accessible names, which results in screen readers not being able to announce what the slider controls to the user, creating an accessibility barrier.
**Action:** When using `QSlider` or similar non-text interactive UI components in Qt/PySide6, always ensure `setAccessibleName()` is explicitly called to provide context for screen readers.
