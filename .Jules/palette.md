## Palette UX Enhancements Journal

## 2024-05-16 - Explicit Accessibility Attributes in Custom Layouts
**Learning:** In PySide6, while `QFormLayout` automatically assigns buddy relationships, standard layouts like `QHBoxLayout` or `QVBoxLayout` require explicitly calling `setBuddy()` to associate labels with inputs. Furthermore, standard interactive elements like `QSlider` do not have accessible names by default, necessitating manual `.setAccessibleName()` calls for proper screen reader announcement.
**Action:** Always explicitly define `.setBuddy()` for labels and `.setAccessibleName()` for standard interactive components when building custom layouts to ensure full screen reader support.
