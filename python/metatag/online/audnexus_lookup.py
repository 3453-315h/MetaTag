"""Audiobook metadata lookup using the Audnexus API."""

import json
import re
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
        self._audible_url = "https://api.audible.com/1.0"
        self._audnexus_url = "https://api.audnex.us"

    def search_books(self, query: str) -> None:
        """Search for audiobooks by title or author using the Audible API."""
        if not query:
            self.lookup_error.emit("Search query cannot be empty")
            return

        # Sanitize query
        clean_query = " ".join(query.split()).strip()

        # Use Audible API for the initial keyword search
        url = QUrl(f"{self._audible_url}/catalog/products")
        q_params = QUrlQuery()
        q_params.addQueryItem("keywords", clean_query)
        q_params.addQueryItem("num_results", "15")
        q_params.addQueryItem("products_sort_by", "Relevance")
        # Include authors and narrators in the search results
        q_params.addQueryItem("response_groups", "contributors,product_attrs")
        url.setQuery(q_params)

        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0 (https://github.com/metatag)")
        request.setRawHeader(b"Accept", b"application/json")

        reply = self._nam.get(request)
        reply.finished.connect(lambda: self._handle_search_reply(reply))

    def search_web_fallback(self, query: str) -> None:
        """Fallback: Search DuckDuckGo for an Audible link and extract the ASIN."""
        search_query = f"{query} site:audible.com"
        url = QUrl("https://duckduckgo.com/html/")
        q_params = QUrlQuery()
        q_params.addQueryItem("q", search_query)
        url.setQuery(q_params)

        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        reply = self._nam.get(request)
        reply.finished.connect(lambda: self._handle_web_fallback_reply(reply))

    def extract_asin(self, text: str) -> Optional[str]:
        """Extract ASIN (B0...) from an Audible URL or raw string."""
        # Standard Audible ASINs start with B0 and are 10 chars long
        match = re.search(r'/(?:pd|asin|product)/.*?/([B0][A-Z0-9]{9})', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        # Fallback for just the ASIN
        match = re.search(r'\b([B0][A-Z0-9]{9})\b', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def fetch_book_details(self, asin: str) -> None:
        """Fetch full details for an audiobook by its ASIN using Audnexus."""
        url = QUrl(f"{self._audnexus_url}/books/{asin}")
        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"MetaTag/1.0 (https://github.com/metatag)")
        
        reply = self._nam.get(request)
        reply.finished.connect(lambda: self._handle_details_reply(reply))

    def _handle_search_reply(self, reply: QNetworkReply) -> None:
        """Handle Audible search results."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.lookup_error.emit(f"Search failed: {reply.errorString()}")
                return

            data = json.loads(reply.readAll().data())
            products = data.get("products", [])
            
            processed = []
            for item in products:
                # Authors and narrators are lists of objects
                authors = item.get("authors", [])
                author_name = authors[0].get("name", "Unknown") if authors else "Unknown"
                
                narrators = item.get("narrators", [])
                narrator_name = narrators[0].get("name", "") if narrators else ""
                
                processed.append({
                    "id": item.get("asin"),
                    "title": item.get("title", "Unknown"),
                    "artist": author_name,
                    "narrator": narrator_name,
                    "series": "", 
                    "year": str(item.get("release_date", ""))[:4],
                })
            
            self.results_fetched.emit(processed)
        except Exception as e:
            self.lookup_error.emit(f"Parse error: {e}")
        finally:
            reply.deleteLater()

    def _handle_web_fallback_reply(self, reply: QNetworkReply) -> None:
        """Parse DuckDuckGo HTML for Audible links."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.lookup_error.emit(f"Web search failed: {reply.errorString()}")
                return

            html = reply.readAll().data().decode("utf-8", errors="ignore")
            # Look for audible.com/pd/ or audible.com/asin/ links
            links = re.findall(r'audible\.com/pd/[^"\'>\s]+', html)
            
            asins = []
            seen = set()
            for link in links:
                asin = self.extract_asin(link)
                if asin and asin not in seen:
                    asins.append(asin)
                    seen.add(asin)
            
            if not asins:
                self.results_fetched.emit([])
                return
                
            # For each ASIN found, we should ideally fetch its basic info to show in the list.
            # But for simplicity, we'll just emit them as "Web Result [ASIN]"
            results = []
            for asin in asins[:5]: # limit to top 5
                results.append({
                    "id": asin,
                    "title": f"Web Result: {asin}",
                    "artist": "Select to load details",
                    "narrator": "",
                    "series": "",
                    "year": "",
                })
            self.results_fetched.emit(results)

        except Exception as e:
            self.lookup_error.emit(f"Web parse error: {e}")
        finally:
            reply.deleteLater()

    def _handle_details_reply(self, reply: QNetworkReply) -> None:
        """Handle full book metadata JSON from Audnexus."""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.lookup_error.emit(f"Fetch failed: {reply.errorString()}")
                return

            data = json.loads(reply.readAll().data())
            
            # Authors and narrators are now arrays of objects
            authors = data.get("authors", [])
            if authors and isinstance(authors, list):
                author_name = ", ".join([a.get("name") for a in authors if isinstance(a, dict) and a.get("name")])
            else:
                author_name = data.get("author", "Unknown")

            narrators = data.get("narrators", [])
            if narrators and isinstance(narrators, list):
                narrator_name = ", ".join([n.get("name") for n in narrators if isinstance(n, dict) and n.get("name")])
            else:
                narrator_name = data.get("narrator", "")

            # Series info is often in seriesPrimary
            series_info = data.get("seriesPrimary") or data.get("series", {})
            if isinstance(series_info, dict):
                series_name = series_info.get("name", "")
            else:
                series_name = str(series_info) if series_info else ""

            # Map Audnex fields to our internal expected format
            details = {
                "title": data.get("title", "Unknown"),
                "artist": author_name,
                "narrator": narrator_name,
                "series": series_name,
                "year": str(data.get("releaseDate", ""))[:4],
                "comment": data.get("description", ""),
                "cover_url": data.get("image"),
                "series_name": series_name,
            }
            
            self.details_fetched.emit(details)
        except Exception as e:
            self.lookup_error.emit(f"Details error: {e}")
        finally:
            reply.deleteLater()
