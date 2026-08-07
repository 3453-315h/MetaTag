## 2024-08-07 - Screen Reader associations in QHBoxLayout
**Learning:** While `QFormLayout` automatically establishes buddy relationships between labels and inputs, manual layouts like `QHBoxLayout` do not. Missing `setBuddy` leaves screen readers without context for inputs.
**Action:** When creating form elements in non-form layouts (like search bars), always use an ampersand (`&`) in the text for keyboard accelerators and explicitly call `label.setBuddy(input_widget)`.
