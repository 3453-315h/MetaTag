## $(date +%Y-%m-%d) - Enable Keyboard Accelerator for Search Bar
**Learning:** In PySide6 applications without explicit layout-based buddy management (like QFormLayout.addRow), standard UI elements like QLineEdit require explicit label.setBuddy() calls. Furthermore, an ampersand (&) in the QLabel text establishes the keyboard shortcut (e.g. Alt+S).
**Action:** Always assign a buddy relationship and use an ampersand for primary action or navigation input labels to ensure quick keyboard accessibility for users.
