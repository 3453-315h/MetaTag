"""Track class for audio file metadata."""

import io
import os
from pathlib import Path
from typing import Any, Optional, Union

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
        self._modified_fields: set[str] = set()
        self._cover_art_modified: bool = False

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def file_path(self) -> Path:
        return self._file_path

    def update_path(self, new_path: Union[str, Path]) -> None:
        """Update the file path after a rename (avoids private-attr access)."""
        self._file_path = Path(new_path)

    @staticmethod
    def _to_int(value: Any) -> int:
        """Coerce strings, ints or floats safely to integer."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            clean = value.strip().split("/")[0].strip()
            clean = clean[:4] if len(clean) >= 4 and clean[:4].isdigit() else clean
            try:
                return int(clean) if clean else 0
            except ValueError:
                return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    @property
    def artist(self) -> str:
        return self._artist

    @artist.setter
    def artist(self, value: str) -> None:
        val_str = str(value) if value is not None else ""
        if self._artist != val_str:
            self._artist = val_str
            self._modified_fields.add("artist")
            self._dirty = True

    @property
    def album(self) -> str:
        return self._album

    @album.setter
    def album(self, value: str) -> None:
        val_str = str(value) if value is not None else ""
        if self._album != val_str:
            self._album = val_str
            self._modified_fields.add("album")
            self._dirty = True

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        val_str = str(value) if value is not None else ""
        if self._title != val_str:
            self._title = val_str
            self._modified_fields.add("title")
            self._dirty = True

    @property
    def track_number(self) -> int:
        return self._track_number

    @track_number.setter
    def track_number(self, value: int) -> None:
        val_int = self._to_int(value)
        if self._track_number != val_int:
            self._track_number = val_int
            self._modified_fields.add("track_number")
            self._dirty = True

    @property
    def track_total(self) -> int:
        return self._track_total

    @track_total.setter
    def track_total(self, value: int) -> None:
        val_int = self._to_int(value)
        if self._track_total != val_int:
            self._track_total = val_int
            self._modified_fields.add("track_total")
            self._dirty = True

    @property
    def disc_number(self) -> int:
        return self._disc_number

    @disc_number.setter
    def disc_number(self, value: int) -> None:
        val_int = self._to_int(value)
        if self._disc_number != val_int:
            self._disc_number = val_int
            self._modified_fields.add("disc_number")
            self._dirty = True

    @property
    def disc_total(self) -> int:
        return self._disc_total

    @disc_total.setter
    def disc_total(self, value: int) -> None:
        val_int = self._to_int(value)
        if self._disc_total != val_int:
            self._disc_total = val_int
            self._modified_fields.add("disc_total")
            self._dirty = True

    @property
    def genre(self) -> str:
        return self._genre

    @genre.setter
    def genre(self, value: str) -> None:
        val_str = str(value) if value is not None else ""
        if self._genre != val_str:
            self._genre = val_str
            self._modified_fields.add("genre")
            self._dirty = True

    @property
    def year(self) -> int:
        return self._year

    @year.setter
    def year(self, value: int) -> None:
        val_int = self._to_int(value)
        if self._year != val_int:
            self._year = val_int
            self._modified_fields.add("year")
            self._dirty = True

    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        val_str = str(value) if value is not None else ""
        if self._comment != val_str:
            self._comment = val_str
            self._modified_fields.add("comment")
            self._dirty = True

    @property
    def composer(self) -> str:
        return self._composer

    @composer.setter
    def composer(self, value: str) -> None:
        val_str = str(value) if value is not None else ""
        if self._composer != val_str:
            self._composer = val_str
            self._modified_fields.add("composer")
            self._dirty = True

    @property
    def grouping(self) -> str:
        return self._grouping

    @grouping.setter
    def grouping(self, value: str) -> None:
        val_str = str(value) if value is not None else ""
        if self._grouping != val_str:
            self._grouping = val_str
            self._modified_fields.add("grouping")
            self._dirty = True

    @property
    def bpm(self) -> int:
        return self._bpm

    @bpm.setter
    def bpm(self, value: int) -> None:
        val_int = self._to_int(value)
        if self._bpm != val_int:
            self._bpm = val_int
            self._modified_fields.add("bpm")
            self._dirty = True

    @property
    def cover_art(self) -> Optional[Image.Image]:
        return self._cover_art

    @cover_art.setter
    def cover_art(self, value: Optional[Image.Image]) -> None:
        self._cover_art = value
        self._cover_art_modified = True
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

            # Raw ID3 override for MP3 comments and WAV/AIFF ID3 tags
            id3 = self._get_id3_tags()
            if id3 is not None:
                if "TIT2" in id3 and id3["TIT2"].text:
                    self._title = str(id3["TIT2"].text[0])
                if "TPE1" in id3 and id3["TPE1"].text:
                    self._artist = str(id3["TPE1"].text[0])
                if "TALB" in id3 and id3["TALB"].text:
                    self._album = str(id3["TALB"].text[0])
                if "TCON" in id3 and id3["TCON"].text:
                    self._genre = str(id3["TCON"].text[0])
                if "TRCK" in id3 and id3["TRCK"].text:
                    self._track_number, self._track_total = self._parse_num_total(str(id3["TRCK"].text[0]))

                date_str = ""
                if "TDRC" in id3 and id3["TDRC"].text:
                    date_str = str(id3["TDRC"].text[0])
                elif "TYER" in id3 and id3["TYER"].text:
                    date_str = str(id3["TYER"].text[0])
                if date_str:
                    year_part = date_str[:4]
                    if year_part.isdigit():
                        self._year = int(year_part)

                comm_frames = id3.getall("COMM")
                if comm_frames:
                    for c in comm_frames:
                        if c.text:
                            self._comment = str(c.text[0])
                            break

            # Additional fields whose easy-interface support is inconsistent
            self._load_additional_fields()

            # Cover art
            self._load_cover_art()

            # Duration
            if self._mutagen_file.info is not None:
                self._duration = int(self._mutagen_file.info.length * 1000)

            self._loaded = True
            self._dirty = False
            self._modified_fields.clear()
            self._cover_art_modified = False
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
        new_img.paste(img)
        self._cover_art = new_img
        self._cover_art_modified = True
        self._dirty = True
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
            if self._cover_art_modified:
                self._save_cover_art()
            self._mutagen_file.save()

            # Restore original timestamps
            if mtime is not None and atime is not None:
                os.utime(self._file_path, (atime, mtime))

            self._dirty = False
            self._modified_fields.clear()
            self._cover_art_modified = False
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
        """Write metadata to an ID3 tag container, updating only touched fields."""
        mods = self._modified_fields
        all_fields = len(mods) == 0

        if all_fields or "artist" in mods:
            id3.add(TPE1(encoding=3, text=[self._artist]))
        if all_fields or "album" in mods:
            id3.add(TALB(encoding=3, text=[self._album]))
        if all_fields or "title" in mods:
            id3.add(TIT2(encoding=3, text=[self._title]))

        if all_fields or "track_number" in mods or "track_total" in mods:
            if track_str:
                id3.add(TRCK(encoding=3, text=[track_str]))
            elif "TRCK" in id3:
                del id3["TRCK"]

        if all_fields or "genre" in mods:
            id3.add(TCON(encoding=3, text=[self._genre]))

        if all_fields or "year" in mods:
            if self._year > 0:
                id3.add(TDRC(encoding=3, text=[str(self._year)]))
            elif "TDRC" in id3:
                del id3["TDRC"]

        if all_fields or "comment" in mods:
            id3.delall("COMM")
            if self._comment:
                id3.add(COMM(encoding=3, lang="eng", desc="", text=[self._comment]))

        if all_fields or "composer" in mods:
            if self._composer:
                id3.add(TCOM(encoding=3, text=[self._composer]))
            elif "TCOM" in id3:
                del id3["TCOM"]

        # TIT1 = "Content group description" (not TXXX)
        if all_fields or "grouping" in mods:
            if self._grouping:
                id3.add(TIT1(encoding=3, text=[self._grouping]))
            elif "TIT1" in id3:
                del id3["TIT1"]

        # TBPM = BPM frame (not TXXX)
        if all_fields or "bpm" in mods:
            if self._bpm > 0:
                id3.add(TBPM(encoding=3, text=[str(self._bpm)]))
            elif "TBPM" in id3:
                del id3["TBPM"]

        if all_fields or "disc_number" in mods or "disc_total" in mods:
            if disc_str:
                id3.add(TPOS(encoding=3, text=[disc_str]))
            elif "TPOS" in id3:
                del id3["TPOS"]

    def _save_vorbis_fields(self, track_str: str, disc_str: str) -> None:
        """Write metadata to a VorbisComment container (shared by FLAC + Ogg*)."""
        f = self._mutagen_file
        mods = self._modified_fields
        all_fields = len(mods) == 0

        # Core fields — only written if modified or all
        if all_fields or "artist" in mods:
            f["artist"] = [self._artist]
        if all_fields or "album" in mods:
            f["album"] = [self._album]
        if all_fields or "title" in mods:
            f["title"] = [self._title]
        if all_fields or "genre" in mods:
            f["genre"] = [self._genre]

        if all_fields or "composer" in mods:
            if self._composer:
                f["composer"] = [str(self._composer)]
            elif "composer" in f:
                del f["composer"]

        if all_fields or "grouping" in mods:
            if self._grouping:
                f["grouping"] = [str(self._grouping)]
            elif "grouping" in f:
                del f["grouping"]

        if all_fields or "track_number" in mods or "track_total" in mods:
            if track_str:
                f["tracknumber"] = [track_str]
            elif "tracknumber" in f:
                del f["tracknumber"]

        if all_fields or "disc_number" in mods or "disc_total" in mods:
            if disc_str:
                f["discnumber"] = [disc_str]
            elif "discnumber" in f:
                del f["discnumber"]

        if all_fields or "year" in mods:
            if self._year > 0:
                f["date"] = [str(self._year)]
            elif "date" in f:
                del f["date"]

        if all_fields or "comment" in mods:
            if self._comment:
                f["comment"] = [self._comment]
            elif "comment" in f:
                del f["comment"]

        if all_fields or "bpm" in mods:
            if self._bpm > 0:
                f["bpm"] = [str(self._bpm)]
            elif "bpm" in f:
                del f["bpm"]

    def _save_mp4_fields(self, track_str: str, disc_str: str) -> None:
        """Write metadata to an MP4/M4A tag container, updating only touched fields."""
        f = self._mutagen_file
        mods = self._modified_fields
        all_fields = len(mods) == 0

        if all_fields or "artist" in mods:
            f["\xa9ART"] = [self._artist]
        if all_fields or "album" in mods:
            f["\xa9alb"] = [self._album]
        if all_fields or "title" in mods:
            f["\xa9nam"] = [self._title]
        if all_fields or "genre" in mods:
            f["\xa9gen"] = [self._genre]

        if all_fields or "composer" in mods:
            if self._composer:
                f["\xa9wrt"] = [self._composer]
            elif "\xa9wrt" in f:
                del f["\xa9wrt"]

        if all_fields or "grouping" in mods:
            if self._grouping:
                f["\xa9grp"] = [self._grouping]
            elif "\xa9grp" in f:
                del f["\xa9grp"]

        if all_fields or "bpm" in mods:
            if self._bpm > 0:
                f["tmpo"] = [self._bpm]
            elif "tmpo" in f:
                del f["tmpo"]

        if all_fields or "comment" in mods:
            if self._comment:
                f["\xa9cmt"] = [self._comment]
            elif "\xa9cmt" in f:
                del f["\xa9cmt"]

        if all_fields or "year" in mods:
            if self._year > 0:
                f["\xa9day"] = [str(self._year)]
            elif "\xa9day" in f:
                del f["\xa9day"]

        if all_fields or "track_number" in mods or "track_total" in mods:
            if self._track_number > 0 or self._track_total > 0:
                f["trkn"] = [(self._track_number or 0, self._track_total or 0)]
            elif "trkn" in f:
                del f["trkn"]

        if all_fields or "disc_number" in mods or "disc_total" in mods:
            if self._disc_number > 0 or self._disc_total > 0:
                f["disk"] = [(self._disc_number or 0, self._disc_total or 0)]
            elif "disk" in f:
                del f["disk"]

    def _save_cover_art(self) -> None:
        """Embed cover art into file, preserving non-front pictures."""
        if not getattr(self, "_cover_art_modified", False):
            return

        if self._cover_art is None:
            self._remove_cover_art()
            return

        try:
            img_bytes = io.BytesIO()
            self._cover_art.save(img_bytes, format="PNG")
            data = img_bytes.getvalue()

            id3 = self._get_id3_tags()
            if id3 is not None:
                non_front = [f for f in id3.getall("APIC") if f.type != 3]
                id3.delall("APIC")
                for f in non_front:
                    id3.add(f)
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
                non_front = [p for p in self._mutagen_file.pictures if p.type != 3]
                self._mutagen_file.clear_pictures()
                for p in non_front:
                    self._mutagen_file.add_picture(p)
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
            raise

    def _remove_cover_art(self) -> None:
        """Remove front cover art from the loaded mutagen file, preserving other pictures."""
        try:
            id3 = self._get_id3_tags()
            if id3 is not None:
                non_front = [f for f in id3.getall("APIC") if f.type != 3]
                id3.delall("APIC")
                for f in non_front:
                    id3.add(f)
                return
            if isinstance(self._mutagen_file, FLAC):
                non_front = [p for p in self._mutagen_file.pictures if p.type != 3]
                self._mutagen_file.clear_pictures()
                for p in non_front:
                    self._mutagen_file.add_picture(p)
                return
            if isinstance(self._mutagen_file, MP4) and "covr" in self._mutagen_file:
                del self._mutagen_file["covr"]
                return
            if isinstance(self._mutagen_file, (OggVorbis, OggOpus)):
                if "metadata_block_picture" in self._mutagen_file:
                    del self._mutagen_file["metadata_block_picture"]
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to remove cover art: {e}")
            raise
