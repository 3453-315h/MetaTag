## 2026-08-20 - Keyboard Accessibility for Search Bar
**Learning:** In PySide6, labels in QHBoxLayouts do not automatically associate with their inputs, breaking screen reader support. Furthermore, without ampersands in label text, users miss out on keyboard accelerators.
**Action:** Explicitly set buddy relationships using `label.setBuddy(input)` and add `&` to label text for shortcuts outside of QFormLayouts.
