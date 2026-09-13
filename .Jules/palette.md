## 2026-09-13 - Audio Player Accessibility Improvements
**Learning:** In PySide6, native UI elements like sliders do not inherently expose accessible names for screen readers, unlike some web-based counterparts. A buddy relationship between a label and a widget via `QLabel.setBuddy()` must be manually established, along with utilizing `setAccessibleName()` to ensure full screen reader compatibility.
**Action:** Always explicitly verify or set `setAccessibleName()`, `setToolTip()`, and `setBuddy()` for input widgets like `QSlider` when adding accessibility to PySide6 UI elements.
