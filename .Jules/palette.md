## 2024-11-20 - Adding Keyboard Nav and Buddy Info in PySide6
**Learning:** In Qt/PySide6, assigning an ampersand (`&`) in a QLabel's text allows for a quick keyboard shortcut via Alt. Pairing this with `setBuddy(widget)` is an optimal semantic accessibility implementation for pairing non-FormLayout inputs to labels.
**Action:** Always prefer using native `setBuddy()` over external workarounds when building custom widget layouts to ensure native OS screen-reader functionality works efficiently.
