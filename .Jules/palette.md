## 2024-05-24 - Accessibility bindings in PySide6
**Learning:** PySide6 layouts like QHBoxLayout don't automatically set up buddy relationships between QLabels and inputs like QFormLayout does, and default UI elements often lack accessible names. This breaks screen readers and keyboard navigation.
**Action:** When creating custom layouts, always manually set accessible names with `setAccessibleName()` and use `setBuddy()` along with ampersand accelerators to tie labels to their corresponding inputs.
