## 2026-08-13 - Add buddy label and keyboard accelerator to search bar
**Learning:** PySide6 accessibility rules state that when creating custom layouts like `QHBoxLayout`, buddy relationships must be explicitly added with `label.setBuddy(widget)`. The keyboard accelerator can be added to the label by including an ampersand (`&`) in the label text.
**Action:** Adding a buddy to the search label and an ampersand to its text (changing "Search:" to "&Search:") improves accessibility by binding `Alt+S` to the search input, allowing screen readers to announce the label when the input gets focus.
