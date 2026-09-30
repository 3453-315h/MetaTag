## 2024-05-18 - QLineEdit standalone label association
**Learning:** In PySide6, standard UI elements like QLineEdit when accompanied by standalone QLabel instances do not have an automatic screen reader association or keyboard accelerator, unlike when using `QFormLayout.addRow()`.
**Action:** Always explicitly use `label.setBuddy(widget)` and include an ampersand (`&`) in the label text to assign keyboard accelerators and establish buddy relationships for screen readers when using non-form layouts like QHBoxLayout.
