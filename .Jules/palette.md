## 2026-08-24 - Adding keyboard accelerator for layouts other than QFormLayout
**Learning:** QFormLayout.addRow() handles buddy relationships automatically for accessibility, but when using manual layouts (like QHBoxLayout for search bars), we must explicitly call label.setBuddy(widget) and add an ampersand to assign keyboard accelerators and screen reader relationships.
**Action:** Always check manual layout constructions containing labels and inputs to ensure setBuddy() is explicitly assigned.
