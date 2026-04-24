<p align="center">
  <img src="assets/logo.png" width="128" height="128" alt="MetaTag Logo">
</p>

# MetaTag - Professional Audio & Audiobook Metadata Management

**MetaTag** is a powerful, cross-platform audio tagging application designed for music collectors, DJs, researchers, and audiobook lovers. Built with a high-performance Model/View architecture, it offers professional-grade metadata management with zero latency, even for massive libraries.

[![Python CI](https://github.com/3453-315h/MetaTag/actions/workflows/python.yml/badge.svg)](https://github.com/3453-315h/MetaTag/actions/workflows/python.yml)
[![Native CI](https://github.com/3453-315h/MetaTag/actions/workflows/ci.yml/badge.svg)](https://github.com/3453-315h/MetaTag/actions/workflows/ci.yml)

---

## 🚀 Key Features

### 🎧 Audio & Audiobook Tagging
- **Multi-Format Support**: Full support for MP3 (ID3v1/v2), FLAC, M4A/MP4 (iTunes), Ogg Vorbis, Opus, WAV, and AIFF.
- **Specialized Audiobook Engine**: Integrated fetching for **Narrators**, **Series**, and **Book Descriptions** via the Audnexus API.
- **Intelligent Field Mapping**: Automatically maps professional audiobook fields (e.g., Narrator to Composer, Series to Grouping).
- **Undo/Redo System**: Full session-wide undo/redo support for all tag edits and file operations.
- **Batch Editing**: Simultaneously update metadata across hundreds of tracks with a single click.

### 🔍 Online Metadata & Discovery
- **Audnexus Integration**: Specialized lookup for audiobooks including high-resolution book covers.
- **MusicBrainz & Discogs**: Connect to official databases for automatic tracklist fetching and deep metadata searches.
- **Adaptive Cover Art Finder**: Automatically download, resize, and embed album art during import.
- **Drag & Drop Covers**: Drag images directly from web browsers or use your clipboard (Ctrl+V) to apply cover art instantly.

### 🛠️ Advanced Automation
- **Tag from Filename**: Extract metadata from complex folder/file structures using custom regex-based patterns.
- **Batch Renaming**: Organize your physical library by renaming and moving files based on their internal metadata.
- **Attribute Preservation**: Option to **Preserve File Modification Timestamps** during tagging operations.

---

## 🎨 User Interface
- **Premium Dark Mode**: A sleek, high-contrast interface designed to reduce eye strain.
- **Customizable Layout**: Toggle and reorder editor fields to suit your specific metadata workflow.
- **Integrated Audio Player**: Preview tracks instantly without switching applications.

---

## 💻 Tech Stack
- **Standard Suite (v1.3.1)**: Built with **Python 3.14+**, **PySide6 (Qt 6)**, and the **Mutagen** metadata engine.
- **Native Implementation**: The original C++/TagLib core is available for high-performance native requirements (see `src/`).

## 🛠️ Usage

### Standalone (Windows)
MetaTag is provided as a standalone, portable application. Simply run the `MetaTag.exe` from the latest release or use the provided installer.

### Developer Setup (Python)
1. Navigate to the `python/` directory.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python run.py`

### Native Build (C++)
Instructions for building the C++ core can be found in [docs/native_build.md](docs/native_build.md).

---

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Developed by MetaTag Team — Precision Metadata for Professional Libraries.*