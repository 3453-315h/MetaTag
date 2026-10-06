## 2024-05-17 - Keyboard Accelerator and Screen Reader Association for Search Bar
**Learning:** Adding a keyboard accelerator (Alt+S) via an ampersand in the text, and explicitly associating the label to the input via `.setBuddy()` significantly improves keyboard navigation and screen reader accessibility for custom UI layouts like QHBoxLayout.
**Action:** Use ampersands in label text for keyboard accelerators and explicitly call `.setBuddy()` to link labels with inputs in non-form layouts.
