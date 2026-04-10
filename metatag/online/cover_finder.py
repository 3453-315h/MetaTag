"""Cover art finder using MusicBrainz and Cover Art Archive."""

import json
import io
from typing import List

from PySide6.QtCore import QObject, Signal, QUrl, QBuffer, QIODevice
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
    QSslError,
)
from PySide6.QtGui import QImage
from PIL import Image

from .musicbrainz_lookup import MusicBrainzLookup


class CoverFinder(QObject):
    """Find cover art for artist/album."""

    cover_fetched = Signal(QImage)  # QImage of cover art
    fetch_error = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._base_url = "https://musicbrainz.org"

    def set_base_url(self, url: str) -> None:
        """Set the base URL for MusicBrainz lookups."""
        self._base_url = url

    def fetch_cover(self, artist: str, album: str) -> None:
        """Fetch cover art for given artist and album."""
        self._artist = artist
        self._album = album
        self._lookup = MusicBrainzLookup(self)
        self._lookup.set_base_url(self._base_url)
        self._lookup.releases_fetched.connect(self._on_releases_fetched)
        self._lookup.lookup_error.connect(
            lambda err: self.fetch_error.emit(f"MusicBrainz lookup failed: {err}")
        )
        self._lookup.lookup_release(artist, album)

    def _on_releases_fetched(self, release_ids: List[str]) -> None:
        """Handle fetched release IDs."""
        if not release_ids:
            self.fetch_error.emit("No releases found for artist/album")
            return
        release_id = release_ids[0]
        self._fetch_cover_art(release_id)

    def _fetch_cover_art(self, release_id: str) -> None:
        """Fetch cover art from Cover Art Archive."""
        url = QUrl(f"https://coverartarchive.org/release/{release_id}")
        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0 (https://github.com/metatag)")
        request.setRawHeader(b"Accept", b"application/json")

        reply = self._nam.get(request)
        reply.sslErrors.connect(self._handle_ssl_errors)
        reply.finished.connect(lambda: self._handle_cover_art_reply(reply))

    def _handle_ssl_errors(self, errors: List[QSslError]) -> None:
        """Handle SSL errors, ignore self-signed certificates."""
        ignorable = []
        for error in errors:
            if error.error() in (
                QSslError.SslError.SelfSignedCertificate,
                QSslError.SslError.SelfSignedCertificateInChain,
            ):
                ignorable.append(error)
        if len(ignorable) == len(errors):
            # All errors are ignorable
            self.sender().ignoreSslErrors(ignorable)

    def _handle_cover_art_reply(self, reply: QNetworkReply) -> None:
        """Handle Cover Art Archive JSON reply."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.fetch_error.emit(
                    f"Cover Art Archive request failed: {reply.errorString()}"
                )
                return

            data = reply.readAll().data()
            if not data:
                self.fetch_error.emit("Empty response from Cover Art Archive")
                return

            result = json.loads(data)
            images = result.get("images", [])
            image_url = None

            # Look for front image first
            for img in images:
                if img.get("front", False):
                    image_url = img.get("image")
                    break

            # If no front image, take first image
            if not image_url and images:
                image_url = images[0].get("image")

            if not image_url:
                self.fetch_error.emit("No cover art found")
                return

            self._download_image(image_url)

        except json.JSONDecodeError as e:
            self.fetch_error.emit(f"Failed to parse Cover Art Archive JSON: {e}")
        except Exception as e:
            self.fetch_error.emit(f"Unexpected error: {e}")
        finally:
            reply.deleteLater()

    def _download_image(self, url: str) -> None:
        """Download image from URL."""
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0 (https://github.com/metatag)")

        reply = self._nam.get(request)
        reply.sslErrors.connect(self._handle_ssl_errors)
        reply.finished.connect(lambda: self._handle_image_reply(reply))

    def _handle_image_reply(self, reply: QNetworkReply) -> None:
        """Handle downloaded image data."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.fetch_error.emit(f"Image download failed: {reply.errorString()}")
                return

            data = reply.readAll().data()
            if not data:
                self.fetch_error.emit("Empty image data")
                return

            # Load as QImage
            image = QImage()
            if not image.loadFromData(data):
                self.fetch_error.emit("Failed to load image data")
                return

            self.cover_fetched.emit(image)

        except Exception as e:
            self.fetch_error.emit(f"Unexpected error: {e}")
        finally:
            reply.deleteLater()

    def qimage_to_pil(self, qimage: QImage) -> Image.Image:
        """Convert QImage to PIL Image entirely in memory (no temp files)."""
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.ReadWrite)
        qimage.save(buf, "PNG")
        buf.seek(0)
        raw = buf.readAll().data()
        buf.close()
        return Image.open(io.BytesIO(raw)).copy()
