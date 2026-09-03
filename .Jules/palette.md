## 2026-09-03 - Audio Player Accessibility
**Learning:** In Qt/PySide6, interactive elements like `QSlider` and custom icon/text buttons lack screen reader context by default. While `QFormLayout` handles label-to-input binding automatically, custom layouts like `QHBoxLayout` require explicit `setBuddy()` calls on `QLabel` elements to link them to their target controls.
**Action:** Always verify that interactive widgets in custom layouts use `setAccessibleName()` and `setToolTip()`, and that associated labels use keyboard accelerators (e.g., '&Vol:') mapped via `setBuddy()`.
