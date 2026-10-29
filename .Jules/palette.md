## 2026-10-29 - PySide6 QSlider Accessibility and Anonymous Labels
**Learning:** PySide6 QSliders default to empty accessible names, creating issues for screen readers. In addition, inline anonymous labels (like `layout.addWidget(QLabel("Vol:"))`) prevent establishing a `.setBuddy()` relationship.
**Action:** Always set `.setAccessibleName()` on standalone sliders. For labels next to inputs, create explicit variables and use `label.setBuddy(input_widget)` with keyboard accelerators (using '&') for better keyboard and screen reader accessibility.
