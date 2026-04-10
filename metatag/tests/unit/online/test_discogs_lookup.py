"""Unit tests for Discogs lookup."""

import pytest
import json
from unittest.mock import Mock, patch
from PySide6.QtCore import QUrl, QUrlQuery
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from metatag.online.discogs_lookup import DiscogsLookup


@pytest.fixture
def lookup():
    """Create a DiscogsLookup instance."""
    return DiscogsLookup()


def test_initialization(lookup):
    """Test DiscogsLookup can be instantiated."""
    assert lookup is not None
    assert isinstance(lookup._nam, QNetworkAccessManager)
    assert lookup._consumer_key is None
    assert lookup._consumer_secret is None
    assert lookup._user_token is None


def test_set_credentials(lookup):
    """Test setting API credentials."""
    lookup.set_credentials(
        consumer_key="key123", consumer_secret="secret456", user_token="token789"
    )
    assert lookup._consumer_key == "key123"
    assert lookup._consumer_secret == "secret456"
    assert lookup._user_token == "token789"


def test_search_releases_empty_artist_album(lookup, qtbot):
    """Test search with empty artist and album emits error."""
    with qtbot.wait_signal(lookup.lookup_error) as blocker:
        lookup.search_releases("", "")

    error_msg = blocker.args[0]
    assert "cannot both be empty" in error_msg


def test_search_releases_constructs_url():
    """Test that search_releases constructs correct URL."""
    lookup = DiscogsLookup()
    with patch.object(QNetworkAccessManager, "get") as mock_get:
        lookup.search_releases("Test Artist", "Test Album")
        mock_get.assert_called_once()
        request = mock_get.call_args[0][0]
        url = request.url().toString()
        assert "api.discogs.com/database/search" in url
        assert "q=Test Artist Test Album" in url
        assert "type=release" in url
        assert "per_page=10" in url


def test_search_releases_with_credentials():
    """Test URL includes credentials when set."""
    lookup = DiscogsLookup()
    lookup.set_credentials(consumer_key="key123", consumer_secret="secret456")
    with patch.object(QNetworkAccessManager, "get") as mock_get:
        lookup.search_releases("Artist", "Album")
        request = mock_get.call_args[0][0]
        url = request.url().toString()
        assert "key=key123" in url
        assert "secret=secret456" in url


def test_handle_reply_finished_success():
    """Test _handle_reply_finished with successful response."""
    lookup = DiscogsLookup()
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.attribute.return_value = None
    mock_reply.readAll.return_value.data.return_value = json.dumps(
        {
            "results": [
                {
                    "id": 123,
                    "title": "Test Album",
                    "year": "2023",
                    "genre": ["Rock"],
                    "style": ["Alternative"],
                    "cover_image": "http://example.com/cover.jpg",
                    "thumb": "http://example.com/thumb.jpg",
                    "artist": [{"name": "Test Artist"}],
                    "label": [{"name": "Test Label"}],
                    "format": ["CD"],
                    "country": "US",
                }
            ]
        }
    ).encode("utf-8")

    captured_releases = []

    def capture(releases):
        captured_releases.extend(releases)

    lookup.releases_fetched.connect(capture)
    lookup._handle_reply_finished(mock_reply)

    assert len(captured_releases) == 1
    release = captured_releases[0]
    assert release["id"] == 123
    assert release["title"] == "Test Album"
    assert release["artist"] == "Test Artist"
    assert release["year"] == "2023"
    assert release["genre"] == "Rock"
    assert release["cover_url"] == "http://example.com/cover.jpg"


def test_handle_reply_finished_no_results():
    """Test _handle_reply_finished when no releases found."""
    lookup = DiscogsLookup()
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.attribute.return_value = None
    mock_reply.readAll.return_value.data.return_value = json.dumps(
        {"results": []}
    ).encode("utf-8")

    captured_error = []
    lookup.lookup_error.connect(captured_error.append)
    lookup._handle_reply_finished(mock_reply)

    assert len(captured_error) == 1
    assert "No releases found" in captured_error[0]


def test_handle_reply_finished_rate_limit():
    """Test _handle_reply_finished with rate limit error."""
    lookup = DiscogsLookup()
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.UnknownNetworkError
    mock_reply.attribute.return_value = 429  # HTTP 429 Too Many Requests
    mock_reply.errorString.return_value = "Too Many Requests"

    captured_error = []
    lookup.lookup_error.connect(captured_error.append)
    lookup._handle_reply_finished(mock_reply)

    assert len(captured_error) == 1
    assert "Rate limit exceeded" in captured_error[0]


def test_extract_artist():
    """Test _extract_artist method."""
    lookup = DiscogsLookup()
    # List of dicts
    release = {"artist": [{"name": "Artist1"}, {"name": "Artist2"}]}
    assert lookup._extract_artist(release) == "Artist1"
    # List of strings
    release = {"artist": ["Artist1", "Artist2"]}
    assert lookup._extract_artist(release) == "Artist1"
    # Empty
    release = {"artist": []}
    assert lookup._extract_artist(release) == ""


def test_extract_label():
    """Test _extract_label method."""
    lookup = DiscogsLookup()
    release = {"label": [{"name": "Label1"}]}
    assert lookup._extract_label(release) == "Label1"
    release = {"label": ["Label1"]}
    assert lookup._extract_label(release) == "Label1"
    release = {"label": []}
    assert lookup._extract_label(release) == ""


if __name__ == "__main__":
    pytest.main([__file__])
