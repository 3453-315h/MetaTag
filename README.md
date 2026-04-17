<p align="center">
  <img src="assets/logo.png" width="128" height="128" alt="MetaTag Logo">
</p>

# MetaTag - Audio Tag Editor for Windows

Cross-platform audio tag editor inspired by macOS Meta (formerly MetaImage). Built with Qt/C++ and TagLib.

## Features

- Batch editing of tags (artist, album, genre, etc.)
- Instant previews with no manual saving
- Support for MP3, FLAC, WAV, AIFF, OGG, MP4, M4A, OGA, SPX
- Track numbering and reordering
- Find & replace with regular expressions
- Online lookups for cover art and missing tags (Discogs, MusicBrainz)
- Pattern-based file renaming and directory organization
- Configurable sidebar layouts
- Drag-and-drop cover art
- CSV import/export
- Library syncing with iTunes, MusicBee, etc.

## Build Status

[![CI](https://github.com/3453-315h/MetaTag/workflows/CI/badge.svg)](https://github.com/3453-315h/MetaTag/actions)

## Build Instructions

### Prerequisites

- Qt 6 (Development packages)
- TagLib C++ library
- CMake 3.16+
- C++17 compiler (MSVC, GCC, Clang)

### Windows

1. Install Qt 6 via Qt Online Installer or vcpkg.
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
4. Build:
   ```bash
   cmake --build . --config Release
   ```
5. (Optional) Build tests:
   ```bash
   cmake .. -DBUILD_TESTS=ON
   cmake --build . --config Release
   ctest
   ```
6. Run the executable `metatag-ui.exe`.

### macOS / Linux

Use your package manager to install Qt6 and TagLib, then follow similar CMake steps.

## License

GPL v3. See LICENSE file.

## Contributing

Welcome! Please open issues and pull requests on GitHub.

## Acknowledgments

- TagLib for audio tagging
- Qt for cross-platform UI
- Meta (macOS) for inspiration