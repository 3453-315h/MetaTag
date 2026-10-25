## 2024-10-25 - QLabel Buddy Relationships
**Learning:** In PySide6 applications, relying on anonymous inline instantiation for labels (e.g., `layout.addWidget(QLabel("Text"))`) prevents the establishment of `buddy` relationships, missing a crucial accessibility opportunity.
**Action:** Always instantiate `QLabel` explicitly as a variable and use `.setBuddy(target_widget)` along with an ampersand (`&`) in the label text to enable screen reader associations and keyboard accelerators.
