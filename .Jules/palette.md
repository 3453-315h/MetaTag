## 2023-10-25 - PySide6 Form Accessibility
**Learning:** Inline anonymous labels (e.g., `layout.addWidget(QLabel('Text'))`) in PySide6 prevent setting `setBuddy()` relationships which are crucial for screen readers and keyboard accessibility.
**Action:** Always instantiate UI labels to variables (e.g., `pattern_label = QLabel('&Pattern:')`) and explicitely associate them with their respective input elements using `.setBuddy(widget)` to improve accessibility.
