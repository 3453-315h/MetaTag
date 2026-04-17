# Native Implementation Build Instructions (C++)

The original MetaTag implementation is built using Qt 6 and C++. This version provides high-performance native tagging using the TagLib library.

## Prerequisites

- **Qt 6** (Development packages: Core, Widgets, Network)
- **TagLib** C++ library
- **CMake** 3.16+
- **C++17** compatible compiler (MSVC, GCC, Clang)

## Build Instructions

### Windows

1. Install Qt 6 via the Qt Online Installer or vcpkg.
2. Install TagLib via vcpkg:
   ```powershell
   vcpkg install taglib
   ```
3. Configure with CMake:
   ```bash
   mkdir build
   cd build
   cmake .. -DCMAKE_TOOLCHAIN_FILE=[path to vcpkg]/scripts/buildsystems/vcpkg.cmake
   ```
4. Build the project:
   ```bash
   cmake --build . --config Release
   ```
5. (Optional) Build and run tests:
   ```bash
   cmake .. -DBUILD_TESTS=ON
   cmake --build . --config Release
   ctest
   ```
6. The executable `metatag-ui.exe` will be located in the `bin` directory.

### macOS / Linux

Use your system package manager to install Qt6 and TagLib, then follow the standard CMake configuration and build steps:

```bash
mkdir build && cd build
cmake ..
make -j$(nproc)
```

## Repository Structure

- `src/core`: Core metadata handling and logic.
- `src/ui`: Qt-based user interface components.
- `src/online`: Metadata lookup engines.
- `src/import`: Tools for importing data from other sources.
- `src/utils`: Supporting utility functions.
