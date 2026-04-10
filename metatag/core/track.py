"""Track class for audio file metadata."""

import io
import os
from pathlib import Path
from typing import Optional, Union

import mutagen
from mutagen.id3 import (
    ID3,
    APIC,
    COMM,
    TALB,
    TBPM,
    TCOM,
    TCON,
    TDRC,
    TIT1,
    TIT2,
    TPOS,
    TPE1,
    TRCK,
)
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Format-adapter tables (FIX #15: replaces per-format copy‑paste in every
# branch of _load_additional_fields / _save_all_fields)
# ---------------------------------------------------------------------------

# Fields that map to a plain VorbisComment / IPTC-style string key in FLAC
# and Ogg.  value = (comment_key,)
_VORBIS_SIMPLE_KEYS: dict[str, str] = {
    "composer": "composer",
    "grouping": "grouping",
    "bpm":      "bpm",
}
_VORBIS_DISC_KEY = "discnumber"

# Fields that map to a single MP4 atom containing a string value
_MP4_SIMPLE_KEYS: dict[str, str] = {
    "artist":   "\xa9ART",
    "album":    "\xa9alb",
    "title":    "\xa9nam",
    "genre":    "\xa9gen",
    "comment":  "\xa9cmt",
    "composer": "\xa9wrt",
    "grouping": "\xa9grp",
}


class Track:
    """Represents audio file metadata."""

    def __init__(self, file_path: Union[str, Path]) -> None:
        self._file_path = Path(file_path)
        self._artist = ""
        self._album = ""
        self._title = ""
        self._track_number = 0
        self._track_total = 0
        self._disc_number = 0
        self._disc_total = 0
        self._genre = ""
        self._year = 0
        self._comment = ""
        self._composer = ""
        self._grouping = ""
        self._bpm = 0
        self._cover_art: Optional[Image.Image] = None
        self._duration = 0
        self._loaded = False
        self._dirty = False
        self._mutagen_file = None

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def file_path(self) -> Path:
        return self._file_path

    def update_path(self, new_path: Union[str, Path]) -> None:
        """Update the file path after a rename (avoids private-attr access)."""
        self._file_path = Path(new_path)

    @property
    def artist(self) -> str:
        return self._artist

    @artist.setter
    def artist(self, value: str) -> None:
        if self._artist != value:
            self._artist = value
            self._dirty = True

    @property
    def album(self) -> str:
        return self._album

    @album.setter
    def album(self, value: str) -> None:
        if self._album != value:
            self._album = value
            self._dirty = True

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if self._title != value:
            self._title = value
            self._dirty = True

    @property
    def track_number(self) -> int:
        return self._track_number

    @track_number.setter
    def track_number(self, value: int) -> None:
        if self._track_number != value:
            self._track_number = value
            self._dirty = True

    @property
    def track_total(self) -> int:
        return self._track_total

    @track_total.setter
    def track_total(self, value: int) -> None:
        if self._track_total != value:
            self._track_total = value
            self._dirty = True

    @property
    def disc_number(self) -> int:
        return self._disc_number

    @disc_number.setter
    def disc_number(self, value: int) -> None:
        if self._disc_number != value:
            self._disc_number = value
            self._dirty = True

    @property
    def disc_total(self) -> int:
        return self._disc_total

    @disc_total.setter
    def disc_total(self, value: int) -> None:
        if self._disc_total != value:
            self._disc_total = value
            self._dirty = True

    @property
    def genre(self) -> str:
        return self._genre

    @genre.setter
    def genre(self, value: str) -> None:
        if self._genre != value:
            self._genre = value
            self._dirty = True

    @property
    def year(self) -> int:
        return self._year

    @year.setter
    def year(self, value: int) -> None:
        if self._year != value:
            self._year = value
            self._dirty = True

    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        if self._comment != value:
            self._comment = value
            self._dirty = True

    @property
    def composer(self) -> str:
        return self._composer

    @composer.setter
    def composer(self, value: str) -> None:
        if self._composer != value:
            self._composer = value
            self._dirty = True

    @property
    def grouping(self) -> str:
        return self._grouping

    @grouping.setter
    def grouping(self, value: str) -> None:
        if self._grouping != value:
            self._grouping = value
            self._dirty = True

    @property
    def bpm(self) -> int:
        return self._bpm

    @bpm.setter
    def bpm(self, value: int) -> None:
        if self._bpm != value:
            self._bpm = value
            self._dirty = True

    @property
    def cover_art(self) -> Optional[Image.Image]:
        return self._cover_art

    @cover_art.setter
    def cover_art(self, value: Optional[Image.Image]) -> None:
        self._cover_art = value
        self._dirty = True

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _get_id3_tags(self) -> Optional[ID3]:
        """Return the underlying ID3 tag object, or None if not an ID3 file.

        mutagen.File() returns format-specific objects (MP3, AIFF, …) whose
        .tags attribute is the actual ID3 instance.  Checking isinstance on
        the *file* object against ID3 is always False; we must inspect .tags.
        """
        tags = getattr(self._mutagen_file, "tags", None)
        if isinstance(tags, ID3):
            return tags
        return None

    @staticmethod
    def _parse_num_total(raw: str) -> tuple[int, int]:
        """Parse 'N' or 'N/T' strings into (number, total) ints."""
        parts = raw.strip().split("/")
        num = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
        total = 0
        if len(parts) > 1 and parts[1].strip().isdigit():
            total = int(parts[1].strip())
        return num, total

    def _is_vorbis_container(self) -> bool:
        """True if the file uses VorbisComment tags (FLAC, Ogg)."""
        return isinstance(self._mutagen_file, (FLAC, OggVorbis, OggOpus))

    # ------------------------------------------------------------------ #
    # Load
    # ------------------------------------------------------------------ #

    def load(self) -> bool:
        """Load metadata from file."""
        try:
            self._mutagen_file = mutagen.File(self._file_path, easy=False)
            if self._mutagen_file is None:
                logger.warning(f"Unsupported file format: {self._file_path}")
                return False

            # Basic tags via the easy interface (consistent across formats)
            easy = mutagen.File(self._file_path, easy=True)
            if easy is not None:
                self._artist = easy.get("artist", [""])[0]
                self._album = easy.get("album", [""])[0]
                self._title = easy.get("title", [""])[0]

                # Track number — easy returns "N/T" for most formats
                track_str = easy.get("tracknumber", ["0"])[0]
                self._track_number, self._track_total = self._parse_num_total(track_str)

                self._genre = easy.get("genre", [""])[0]

                # Year — easy returns full date strings; take first 4 chars
                year_str = easy.get("date", [""])[0][:4]
                self._year = int(year_str) if year_str.isdigit() else 0

                self._comment = easy.get("comment", [""])[0]

            # Additional fields whose easy-interface support is inconsistent
            self._load_additional_fields()

            # Cover art
            self._load_cover_art()

            # Duration
            if self._mutagen_file.info is not None:
                self._duration = int(self._mutagen_file.info.length * 1000)

            self._loaded = True
            self._dirty = False
            return True

        except Exception as e:
            logger.error(f"Failed to load {self._file_path}: {e}")
            return False

    def _load_additional_fields(self) -> None:
        """Load composer, grouping, BPM, disc number/total.

        FIX #15: FLAC and Ogg now share _load_vorbis_extra() instead of
        repeating identical key lookups in separate branches.
        """

        # ---- ID3 (MP3, AIFF, WAV, etc.) --------------------------------
        id3 = self._get_id3_tags()
        if id3 is not None:
            if "TCOM" in id3:
                self._composer = str(id3["TCOM"].text[0])
            if "TIT1" in id3:
                self._grouping = str(id3["TIT1"].text[0])
            if "TBPM" in id3:
                try:
                    self._bpm = int(str(id3["TBPM"].text[0]))
                except (ValueError, TypeError):
                    pass
            if "TPOS" in id3:
                self._disc_number, self._disc_total = self._parse_num_total(
                    str(id3["TPOS"].text[0])
                )
            # Re-parse TRCK for track_total (easy may have missed it)
            if "TRCK" in id3:
                num, total = self._parse_num_total(str(id3["TRCK"].text[0]))
                if self._track_number == 0:
                    self._track_number = num
                if self._track_total == 0:
                    self._track_total = total
            return

        # ---- MP4 / M4A --------------------------------------------------
        if isinstance(self._mutagen_file, MP4):
            self._load_mp4_extra()
            return

        # ---- FLAC  /  Ogg Vorbis  /  Ogg Opus  -------------------------
        # All three use VorbisComment tags; share a single helper.
        if self._is_vorbis_container():
            self._load_vorbis_extra()

    def _load_vorbis_extra(self) -> None:
        """Load extra fields from a VorbisComment container (FLAC, Ogg*)."""
        f = self._mutagen_file
        for attr, key in _VORBIS_SIMPLE_KEYS.items():
            if key in f:
                try:
                    value = f[key][0]
                    if attr == "bpm":
                        self._bpm = int(value)
                    else:
                        setattr(self, f"_{attr}", value)
                except (ValueError, TypeError, AttributeError):
                    pass

        if _VORBIS_DISC_KEY in f:
            self._disc_number, self._disc_total = self._parse_num_total(f[_VORBIS_DISC_KEY][0])

        # FLAC-only totaldiscs fallback tag
        if isinstance(self._mutagen_file, FLAC) and "totaldiscs" in f and self._disc_total == 0:
            try:
                self._disc_total = int(f["totaldiscs"][0])
            except (ValueError, TypeError):
                pass

    def _load_mp4_extra(self) -> None:
        """Load extra fields from an MP4 container."""
        f = self._mutagen_file
        # Composer: ©wrt is standard; ©com is a non-standard fallback
        if "\xa9wrt" in f:
            self._composer = f["\xa9wrt"][0]
        elif "\xa9com" in f:
            self._composer = f["\xa9com"][0]
        if "\xa9grp" in f:
            self._grouping = f["\xa9grp"][0]
        if "tmpo" in f:
            try:
                self._bpm = int(f["tmpo"][0])
            except (ValueError, TypeError):
                pass
        # trkn: list of (number, total) tuples
        if "trkn" in f:
            trkn = f["trkn"]
            if trkn and isinstance(trkn[0], (tuple, list)):
                self._track_number = trkn[0][0] or 0
                if len(trkn[0]) >= 2:
                    self._track_total = trkn[0][1] or 0
        if "disk" in f:
            disk = f["disk"]
            if disk and isinstance(disk[0], (tuple, list)):
                self._disc_number = disk[0][0] or 0
                if len(disk[0]) >= 2:
                    self._disc_total = disk[0][1] or 0

    def _load_cover_art(self) -> None:
        """Extract cover art from file."""

        # ---- ID3 --------------------------------------------------------
        id3 = self._get_id3_tags()
        if id3 is not None:
            apic_frames = [f for f in id3.values() if isinstance(f, APIC)]
            # Prefer front cover (type=3), fall back to first available
            apic_frames.sort(key=lambda f: (0 if f.type == 3 else 1))
            if apic_frames:
                try:
                    image = Image.open(io.BytesIO(apic_frames[0].data))
                    if image.mode not in ("RGB", "RGBA"):
                        image = image.convert("RGB")
                    self._cover_art = image
                    logger.info(f"Loaded cover art from ID3: {self._file_path}")
                except Exception as e:
                    logger.warning(f"Failed to load cover art from ID3: {e}")
            return

        # ---- FLAC -------------------------------------------------------
        if isinstance(self._mutagen_file, FLAC):
            pictures = self._mutagen_file.pictures
            if pictures:
                front = next((p for p in pictures if p.type == 3), pictures[0])
                try:
                    image = Image.open(io.BytesIO(front.data))
                    if image.mode not in ("RGB", "RGBA"):
                        image = image.convert("RGB")
                    self._cover_art = image
                    logger.info(f"Loaded cover art from FLAC: {self._file_path}")
                except Exception as e:
                    logger.warning(f"Failed to load cover art from FLAC: {e}")
            return

        # ---- MP4 --------------------------------------------------------
        if isinstance(self._mutagen_file, MP4):
            if "covr" in self._mutagen_file:
                data = bytes(self._mutagen_file["covr"][0])
                try:
                    image = Image.open(io.BytesIO(data))
                    if image.mode not in ("RGB", "RGBA"):
                        image = image.convert("RGB")
                    self._cover_art = image
                    logger.info(f"Loaded cover art from MP4: {self._file_path}")
                except Exception as e:
                    logger.warning(f"Failed to load cover art from MP4: {e}")
            return

        # ---- Ogg Vorbis / Opus ------------------------------------------
        if isinstance(self._mutagen_file, (OggVorbis, OggOpus)):
            if "metadata_block_picture" in self._mutagen_file:
                import base64
                try:
                    b64_data = self._mutagen_file["metadata_block_picture"][0]
                    picture = Picture(base64.b64decode(b64_data))
                    image = Image.open(io.BytesIO(picture.data))
                    if image.mode not in ("RGB", "RGBA"):
                        image = image.convert("RGB")
                    self._cover_art = image
                    logger.info(f"Loaded cover art from Ogg: {self._file_path}")
                except Exception as e:
                    logger.warning(f"Failed to load cover art from Ogg: {e}")

        if self._cover_art is None:
            logger.debug(f"No cover art found in {self._file_path}")

    # ------------------------------------------------------------------ #
    # Save
    # ------------------------------------------------------------------ #

    def optimize_cover(self, max_size: int = 800) -> bool:
        """Resize cover art to a max dimension and strip metadata."""
        if not self._cover_art:
            return False
            
        img = self._cover_art
        if img.width <= max_size and img.height <= max_size:
            # Already small enough, but let's re-save to strip EXIF
            pass
            
        # Resize maintaining aspect ratio
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Strip metadata by creating a new image
        new_img = Image.new(img.mode, img.size)
        new_img.putdata(img.getdata())
        self._cover_art = new_img
        return True

    def save(self, preserve_timestamps: bool = False) -> bool:
        """Save metadata back to file."""
        if not self._dirty:
            return True

        # Capture original timestamps if requested
        mtime = None
        atime = None
        if preserve_timestamps and self._file_path.exists():
            stat = self._file_path.stat()
            mtime = stat.st_mtime
            atime = stat.st_atime

        try:
            # Single open → single save; no double-write race
            self._mutagen_file = mutagen.File(self._file_path, easy=False)
            if self._mutagen_file is None:
                return False

            # Ensure tag container exists (e.g. MP3 with no prior ID3 tags)
            if self._mutagen_file.tags is None:
                self._mutagen_file.add_tags()

            self._save_all_fields()
            self._save_cover_art()
            self._mutagen_file.save()

            # Restore original timestamps
            if mtime is not None and atime is not None:
                os.utime(self._file_path, (atime, mtime))

            self._dirty = False
            return True

        except Exception as e:
            logger.error(f"Failed to save {self._file_path}: {e}")
            return False

    def _save_all_fields(self) -> None:
        """Write every metadata field through the single non-easy handle.

        FIX #15: FLAC and Ogg now share _save_vorbis_fields() instead of
        repeating ~30 identical lines in separate branches.
        """

        # Build "X/Y" strings for track and disc
        track_str = str(self._track_number) if self._track_number > 0 else ""
        if self._track_total > 0:
            track_str = f"{self._track_number}/{self._track_total}"

        disc_str = str(self._disc_number) if self._disc_number > 0 else ""
        if self._disc_total > 0:
            disc_str = f"{self._disc_number}/{self._disc_total}"

        # ---- ID3 (MP3, AIFF, WAV, …) ------------------------------------
        id3 = self._get_id3_tags()
        if id3 is not None:
            self._save_id3_fields(id3, track_str, disc_str)
            return

        # ---- MP4 / M4A --------------------------------------------------
        if isinstance(self._mutagen_file, MP4):
            self._save_mp4_fields(track_str, disc_str)
            return

        # ---- FLAC  /  Ogg Vorbis  /  Ogg Opus  -------------------------
        if self._is_vorbis_container():
            self._save_vorbis_fields(track_str, disc_str)

    def _save_id3_fields(self, id3: ID3, track_str: str, disc_str: str) -> None:
        """Write metadata to an ID3 tag container."""
        id3.add(TPE1(encoding=3, text=[self._artist]))
        id3.add(TALB(encoding=3, text=[self._album]))
        id3.add(TIT2(encoding=3, text=[self._title]))

        if track_str:
            id3.add(TRCK(encoding=3, text=[track_str]))
        elif "TRCK" in id3:
            del id3["TRCK"]

        id3.add(TCON(encoding=3, text=[self._genre]))

        if self._year > 0:
            id3.add(TDRC(encoding=3, text=[str(self._year)]))
        elif "TDRC" in id3:
            del id3["TDRC"]

        id3.delall("COMM")
        if self._comment:
            id3.add(COMM(encoding=3, lang="eng", desc="", text=[self._comment]))

        if self._composer:
            id3.add(TCOM(encoding=3, text=[self._composer]))
        elif "TCOM" in id3:
            del id3["TCOM"]

        # TIT1 = "Content group description" (not TXXX)
        if self._grouping:
            id3.add(TIT1(encoding=3, text=[self._grouping]))
        elif "TIT1" in id3:
            del id3["TIT1"]

        # TBPM = BPM frame (not TXXX)
        if self._bpm > 0:
            id3.add(TBPM(encoding=3, text=[str(self._bpm)]))
        elif "TBPM" in id3:
            del id3["TBPM"]

        if disc_str:
            id3.add(TPOS(encoding=3, text=[disc_str]))
        elif "TPOS" in id3:
            del id3["TPOS"]

    def _save_vorbis_fields(self, track_str: str, disc_str: str) -> None:
        """Write metadata to a VorbisComment container (shared by FLAC + Ogg*).

        FIX #15: previously FLAC and Ogg each had ~30 identical lines.
        """
        f = self._mutagen_file

        # Core fields — always written (empty string clears them)
        f["artist"] = [self._artist]
        f["album"]  = [self._album]
        f["title"]  = [self._title]
        f["genre"]  = [self._genre]

        # Optional string fields using the VorbisComment dispatch table
        _str_fields: dict[str, str | int] = {
            "composer": self._composer,
            "grouping": self._grouping,
        }
        for comment_key, value in _str_fields.items():
            if value:
                f[comment_key] = [str(value)]
            elif comment_key in f:
                del f[comment_key]

        # Track/disc X/Y strings
        if track_str:
            f["tracknumber"] = [track_str]
        elif "tracknumber" in f:
            del f["tracknumber"]

        if disc_str:
            f["discnumber"] = [disc_str]
        elif "discnumber" in f:
            del f["discnumber"]

        # Year
        if self._year > 0:
            f["date"] = [str(self._year)]
        elif "date" in f:
            del f["date"]

        # Comment
        if self._comment:
            f["comment"] = [self._comment]
        elif "comment" in f:
            del f["comment"]

        # BPM
        if self._bpm > 0:
            f["bpm"] = [str(self._bpm)]
        elif "bpm" in f:
            del f["bpm"]

    def _save_mp4_fields(self, track_str: str, disc_str: str) -> None:
        """Write metadata to an MP4/M4A tag container."""
        f = self._mutagen_file

        f["\xa9ART"] = [self._artist]
        f["\xa9alb"] = [self._album]
        f["\xa9nam"] = [self._title]
        f["\xa9gen"] = [self._genre]

        # trkn / disk are stored as lists of (number, total) tuples
        f["trkn"] = [(self._track_number or 0, self._track_total or 0)]

        optional_str = {
            "\xa9day": str(self._year) if self._year > 0 else "",
            "\xa9cmt": self._comment,
            "\xa9wrt": self._composer,   # standard Apple composer atom
            "\xa9grp": self._grouping,
        }
        for atom, value in optional_str.items():
            if value:
                f[atom] = [value]
            elif atom in f:
                del f[atom]

        # BPM stored as int, not string
        if self._bpm > 0:
            f["tmpo"] = [self._bpm]
        elif "tmpo" in f:
            del f["tmpo"]

        # Disc number
        if self._disc_number > 0 or self._disc_total > 0:
            f["disk"] = [(self._disc_number or 0, self._disc_total or 0)]
        elif "disk" in f:
            del f["disk"]

    def _save_cover_art(self) -> None:
        """Embed cover art into file."""
        if self._cover_art is None:
            self._remove_cover_art()
            return

        try:
            img_bytes = io.BytesIO()
            self._cover_art.save(img_bytes, format="PNG")
            data = img_bytes.getvalue()

            id3 = self._get_id3_tags()
            if id3 is not None:
                id3.delall("APIC")
                id3.add(
                    APIC(
                        encoding=3,
                        mime="image/png",
                        type=3,
                        desc="Front cover",
                        data=data,
                    )
                )
                return

            if isinstance(self._mutagen_file, FLAC):
                self._mutagen_file.clear_pictures()
                pic = Picture()
                pic.type = 3
                pic.mime = "image/png"
                pic.data = data
                self._mutagen_file.add_picture(pic)
                return

            if isinstance(self._mutagen_file, MP4):
                self._mutagen_file["covr"] = [MP4Cover(data, MP4Cover.FORMAT_PNG)]
                return

            if isinstance(self._mutagen_file, (OggVorbis, OggOpus)):
                import base64
                pic = Picture()
                pic.type = 3
                pic.mime = "image/png"
                pic.data = data
                self._mutagen_file["metadata_block_picture"] = [
                    base64.b64encode(pic.write()).decode("ascii")
                ]

        except Exception as e:
            logger.error(f"Failed to save cover art: {e}")

    def _remove_cover_art(self) -> None:
        """Remove existing cover art from the loaded mutagen file."""
        try:
            id3 = self._get_id3_tags()
            if id3 is not None:
                id3.delall("APIC")
                return
            if isinstance(self._mutagen_file, FLAC):
                self._mutagen_file.clear_pictures()
                return
            if isinstance(self._mutagen_file, MP4) and "covr" in self._mutagen_file:
                del self._mutagen_file["covr"]
                return
            if isinstance(self._mutagen_file, (OggVorbis, OggOpus)):
                if "metadata_block_picture" in self._mutagen_file:
                    del self._mutagen_file["metadata_block_picture"]
        except (ValueError, TypeError):
            pass
