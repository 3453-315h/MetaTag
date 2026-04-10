"""Discogs lookup for release information and cover art."""

import json
from typing import List, Dict, Any

from PySide6.QtCore import QObject, Signal, QUrl, QUrlQuery
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
    QSslError,
)


class DiscogsLookup(QObject):
    """Lookup Discogs releases by artist/album."""

    releases_fetched = Signal(list)  # list of release dicts
    lookup_error = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        # Optional API credentials (for higher rate limits and images)
        self._consumer_key = None
        self._consumer_secret = None
        self._user_token = None

    def set_credentials(
        self,
        consumer_key: str = None,
        consumer_secret: str = None,
        user_token: str = None,
    ) -> None:
        """Set Discogs API credentials."""
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._user_token = user_token

    def search_releases(self, artist: str = "", album: str = "") -> None:
        """Search releases for given artist and album."""
        if not artist and not album:
            self.lookup_error.emit("Artist and album cannot both be empty")
            return

        url = QUrl("https://api.discogs.com/database/search")
        query = QUrlQuery()

        # Build query string: combine artist and album
        query_parts = []
        if artist:
            query_parts.append(artist)
        if album:
            query_parts.append(album)
        query_string = " ".join(query_parts)
        query.addQueryItem("q", query_string)
        query.addQueryItem("type", "release")
        query.addQueryItem("per_page", "10")  # Limit results

        # Add credentials if available
        if self._user_token:
            query.addQueryItem("token", self._user_token)
        elif self._consumer_key and self._consumer_secret:
            query.addQueryItem("key", self._consumer_key)
            query.addQueryItem("secret", self._consumer_secret)

        url.setQuery(query)

        request = QNetworkRequest(url)
        # Discogs requires a unique User-Agent
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0 (https://github.com/metatag)")
        request.setRawHeader(b"Accept", b"application/json")

        reply = self._nam.get(request)
        reply.sslErrors.connect(self._handle_ssl_errors)
        reply.finished.connect(lambda: self._handle_reply_finished(reply))

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

    def _handle_reply_finished(self, reply: QNetworkReply) -> None:
        """Handle finished network reply."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                error_msg = reply.errorString()
                # Check for rate limiting
                if (
                    reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
                    == 429
                ):
                    error_msg = "Rate limit exceeded. Please try again later."
                self.lookup_error.emit(error_msg)
                return

            data = reply.readAll().data()
            if not data:
                self.lookup_error.emit("Empty response from Discogs")
                return

            result = json.loads(data)
            releases = result.get("results", [])
            if not releases:
                self.lookup_error.emit("No releases found for artist/album")
                return

            # Extract relevant release information
            release_info = []
            for release in releases:
                info = {
                    "id": release.get("id"),
                    "title": release.get("title", ""),
                    "year": release.get("year", ""),
                    "genre": ", ".join(release.get("genre", [])),
                    "style": ", ".join(release.get("style", [])),
                    "cover_url": release.get("cover_image", ""),
                    "thumb_url": release.get("thumb", ""),
                    "artist": self._extract_artist(release),
                    "label": self._extract_label(release),
                    "format": ", ".join(release.get("format", [])),
                    "country": release.get("country", ""),
                }
                release_info.append(info)

            self.releases_fetched.emit(release_info)

        except json.JSONDecodeError as e:
            self.lookup_error.emit(f"Failed to parse Discogs JSON: {e}")
        except Exception as e:
            self.lookup_error.emit(f"Unexpected error: {e}")
        finally:
            reply.deleteLater()

    def _extract_artist(self, release: Dict[str, Any]) -> str:
        """Extract artist name from release."""
        artists = release.get("artist", [])
        if isinstance(artists, list) and artists:
            # Could be list of artist strings or dicts
            first = artists[0]
            if isinstance(first, dict):
                return first.get("name", "")
            return str(first)
        return ""

    def _extract_label(self, release: Dict[str, Any]) -> str:
        """Extract label name from release."""
        labels = release.get("label", [])
        if isinstance(labels, list) and labels:
            first = labels[0]
            if isinstance(first, dict):
                return first.get("name", "")
            return str(first)
        return ""
