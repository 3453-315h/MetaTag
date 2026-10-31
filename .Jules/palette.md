## 2024-11-23 - QSlider Accessible Names and Labels
**Learning:** Standard UI elements like QSlider default to having an empty accessibleName. Furthermore, inline anonymous labels prevent setting .setBuddy() relationships.
**Action:** Always explicitly set .setAccessibleName() for sliders and instantiate labels as variables to enable .setBuddy() connections with target widgets.
