## 2024-10-22 - Explicit Accessibility Attributes for Custom PySide6 Layouts
**Learning:** In PySide6, simple elements like `QSlider` do not have accessible names by default. Also, creating inline anonymous labels (e.g., `layout.addWidget(QLabel("Vol:"))`) prevents you from explicitly setting buddy relationships which are crucial for keyboard accessibility (accelerators) and screen reader support.
**Action:** Always instantiate labels as variables (`vol_label = QLabel("&Vol:")`), attach them using `.setBuddy()`, and give interactive elements like `QSlider` an explicit `.setAccessibleName()`.
