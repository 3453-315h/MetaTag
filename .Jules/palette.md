
## 2024-10-24 - Qt Accessibility Defaults
**Learning:** PySide6 default components like QSlider have empty `accessibleName` properties and generic layout items (like inline labels) do not associate with inputs. Keyboard users miss out on shortcuts without explicit ampersands (`&`) in labels.
**Action:** Use `.setAccessibleName()` for standalone interactive widgets. Avoid inline anonymous labels (`QLabel('Text')`); instead, instantiate labels, apply a shortcut with `&`, and use `.setBuddy(widget)` to link them for screen readers and keyboard accessibility.
