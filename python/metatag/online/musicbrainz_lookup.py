"""MusicBrainz lookup for release information."""

import json
from typing import List

from PySide6.QtCore import QObject, Signal, QUrl, QUrlQuery
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
    QSslError,
)


class MusicBrainzLookup(QObject):
    """Lookup MusicBrainz releases by artist/album."""

    releases_fetched = Signal(list)  # list of release IDs
    lookup_error = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._base_url = "https://musicbrainz.org"

    def set_base_url(self, url: str) -> None:
        """Set the base URL for MusicBrainz API requests."""
        if not url:
            self._base_url = "https://musicbrainz.org"
            return
        # Normalize: strip trailing slashes
        self._base_url = url.strip().rstrip("/")

    def lookup_release(self, artist: str, album: str) -> None:
        """Lookup releases for given artist and album."""
        if not artist and not album:
            self.lookup_error.emit("Artist and album cannot both be empty")
            return

        url_str = f"{self._base_url}/ws/2/release/"
        url = QUrl(url_str)
        query = QUrlQuery()
        query_parts = []
        if artist:
            query_parts.append(f'artist:"{artist}"')
        if album:
            query_parts.append(f'release:"{album}"')
        query.addQueryItem("query", " AND ".join(query_parts))
        query.addQueryItem("fmt", "json")
        url.setQuery(query)

        request = QNetworkRequest(url)
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
                self.lookup_error.emit(reply.errorString())
                return

            data = reply.readAll().data()
            if not data:
                self.lookup_error.emit("Empty response from MusicBrainz")
                return

            result = json.loads(data)
            releases = result.get("releases", [])
            release_info = []
            for release in releases:
                # FIX: guard empty artist-credit / label-info lists before [0]
                artist_credits = release.get("artist-credit") or []
                label_info     = release.get("label-info") or []
                info = {
                    "id":      release.get("id"),
                    "title":   release.get("title", ""),
                    "artist":  artist_credits[0].get("name", "") if artist_credits else "",
                    "year":    release.get("date", "")[:4],
                    "label":   label_info[0].get("label", {}).get("name", "") if label_info else "",
                    "country": release.get("country", ""),
                }
                release_info.append(info)

            if not release_info:
                self.lookup_error.emit("No releases found for artist/album")
                return

            self.releases_fetched.emit(release_info)

        except json.JSONDecodeError as e:
            self.lookup_error.emit(f"Failed to parse MusicBrainz JSON: {e}")
        except Exception as e:
            self.lookup_error.emit(f"Unexpected error: {e}")

    def fetch_release_details(self, release_id: str) -> None:
        """Fetch detailed information (tracklist) for a specific release."""
        url_str = f"{self._base_url}/ws/2/release/{release_id}"
        url = QUrl(url_str)
        query = QUrlQuery()
        query.addQueryItem("inc", "recordings+artist-credits")
        query.addQueryItem("fmt", "json")
        url.setQuery(query)

        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0 (https://github.com/metatag)")
        reply = self._nam.get(request)
        reply.finished.connect(lambda: self._handle_details_reply(reply))

    def _handle_details_reply(self, reply: QNetworkReply) -> None:
        """Parse the detailed release JSON."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.lookup_error.emit(reply.errorString())
                return
            
            data = json.loads(reply.readAll().data())
            tracks = []
            for medium in data.get("media", []):
                for track in medium.get("tracks", []):
                    # FIX: guard empty artist-credit before [0] access
                    t_credits = track.get("artist-credit") or []
                    tracks.append({
                        "title":  track.get("title", ""),
                        "artist": t_credits[0].get("name", "") if t_credits else "",
                        "number": track.get("position", ""),
                    })

            # FIX: guard release-level artist-credit before [0] access
            r_credits = data.get("artist-credit") or []
            self.releases_fetched.emit([{
                "title":  data.get("title"),
                "artist": r_credits[0].get("name", "") if r_credits else "",
                "tracks": tracks,
            }])
        except Exception as e:
            self.lookup_error.emit(f"Details error: {e}")
        finally:
            reply.deleteLater()
