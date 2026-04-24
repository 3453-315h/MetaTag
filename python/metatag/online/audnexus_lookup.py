"""Audiobook metadata lookup using the Audnexus API."""

import json
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal, QUrl, QUrlQuery
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
)

class AudiobookLookup(QObject):
    """Lookup audiobook metadata via Audnexus / Audnex API."""

    results_fetched = Signal(list)  # List of book search results
    details_fetched = Signal(dict)  # Full book metadata
    lookup_error = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._base_url = "https://api.audnex.us"

    def search_books(self, query: str) -> None:
        """Search for audiobooks by title or author."""
        if not query:
            self.lookup_error.emit("Search query cannot be empty")
            return

        # Sanitize query: replace newlines, tabs, and multiple spaces with a single space
        clean_query = " ".join(query.split()).strip()

        # The current Audnex API uses /authors?name=... for general search
        url = QUrl(f"{self._base_url}/authors")
        q_params = QUrlQuery()
        q_params.addQueryItem("name", clean_query)
        url.setQuery(q_params)

        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0 (https://github.com/metatag)")
        request.setRawHeader(b"Accept", b"application/json")

        reply = self._nam.get(request)
        reply.finished.connect(lambda: self._handle_search_reply(reply))

    def fetch_book_details(self, asin: str) -> None:
        """Fetch full details for an audiobook by its ASIN."""
        url = QUrl(f"{self._base_url}/books/{asin}")
        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0 (https://github.com/metatag)")
        
        reply = self._nam.get(request)
        reply.finished.connect(lambda: self._handle_details_reply(reply))

    def _handle_search_reply(self, reply: QNetworkReply) -> None:
        """Handle JSON search results."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.lookup_error.emit(f"Search failed: {reply.errorString()}")
                return

            data = json.loads(reply.readAll().data())
            # Audnex search results are usually a direct list of items
            results = data if isinstance(data, list) else data.get("results", [])
            
            processed = []
            for item in results:
                processed.append({
                    "id": item.get("asin"),
                    "title": item.get("name", item.get("title", "Unknown")),
                    "artist": item.get("author", "Unknown"),
                    "narrator": item.get("narrator", ""),
                    "series": item.get("series", ""),
                    "year": str(item.get("releaseDate", ""))[:4],
                })
            
            self.results_fetched.emit(processed)
        except Exception as e:
            self.lookup_error.emit(f"Parse error: {e}")
        finally:
            reply.deleteLater()

    def _handle_details_reply(self, reply: QNetworkReply) -> None:
        """Handle full book metadata JSON."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.lookup_error.emit(f"Fetch failed: {reply.errorString()}")
                return

            data = json.loads(reply.readAll().data())
            
            # Map Audnex fields to our internal expected format
            details = {
                "title": data.get("title"),
                "artist": data.get("author"),
                "narrator": data.get("narrator"),
                "series": data.get("series"),
                "year": data.get("releaseDate", "")[:4],
                "comment": data.get("description", ""),
                "cover_url": data.get("image"),
                # Handle series structure if it's nested
                "series_name": data.get("series", {}).get("name") if isinstance(data.get("series"), dict) else data.get("series"),
            }
            
            self.details_fetched.emit(details)
        except Exception as e:
            self.lookup_error.emit(f"Details error: {e}")
        finally:
            reply.deleteLater()
