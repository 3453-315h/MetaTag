## 2023-11-01 - QLineEdit Accessibility in PySide6
**Learning:** Standard UI elements like QLineEdit when used with QLabels in PySide6 lack automatic accessible names and screen reader associations unless explicitly configured.
**Action:** When creating a QLabel alongside an input like QLineEdit, always instantiate the label as a variable, add an ampersand to its text for a keyboard shortcut, explicitly call `label.setBuddy(input_widget)`, and ensure the input widget has `.setAccessibleName()` called on it.
