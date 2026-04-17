"""Unit tests for CoverFinder."""

import pytest
import json
from unittest.mock import Mock, patch, PropertyMock
from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtGui import QImage
from PIL import Image
import io

from metatag.online.cover_finder import CoverFinder
from metatag.online.musicbrainz_lookup import MusicBrainzLookup


@pytest.fixture
def finder():
    """Create a CoverFinder instance."""
    return CoverFinder()


def test_initialization(finder):
    """Test CoverFinder can be instantiated."""
    assert finder is not None
    assert isinstance(finder._nam, QNetworkAccessManager)


def test_fetch_cover_empty_artist_album(finder, qtbot):
    """Test fetch_cover with empty artist and album emits error."""
    # MusicBrainzLookup.lookup_release will emit lookup_error signal,
    # which is connected to finder.fetch_error.
    with qtbot.wait_signal(finder.fetch_error) as blocker:
        finder.fetch_cover("", "")
    error_msg = blocker.args[0]
    assert "MusicBrainz lookup failed" in error_msg


def test_fetch_cover_triggers_lookup(finder):
    """Test fetch_cover creates MusicBrainzLookup and calls lookup_release."""
    with patch.object(MusicBrainzLookup, "__init__", return_value=None) as mock_init:
        with patch.object(MusicBrainzLookup, "lookup_release") as mock_lookup:
            with patch.object(MusicBrainzLookup, "releases_fetched"):
                with patch.object(MusicBrainzLookup, "lookup_error"):
                    finder.fetch_cover("Test Artist", "Test Album")
                    mock_init.assert_called_once()
                    mock_lookup.assert_called_once_with("Test Artist", "Test Album")


def test_on_releases_fetched_empty_list(finder, qtbot):
    """Test _on_releases_fetched with empty list emits error."""
    with qtbot.wait_signal(finder.fetch_error) as blocker:
        finder._on_releases_fetched([])
    error_msg = blocker.args[0]
    assert "No releases found" in error_msg


def test_on_releases_fetched_triggers_fetch_cover_art(finder):
    """Test _on_releases_fetched calls _fetch_cover_art with first release ID."""
    with patch.object(finder, "_fetch_cover_art") as mock_fetch:
        finder._on_releases_fetched(["release-123", "release-456"])
        mock_fetch.assert_called_once_with("release-123")


def test_fetch_cover_art_constructs_url(finder):
    """Test _fetch_cover_art constructs correct Cover Art Archive URL."""
    with patch.object(QNetworkAccessManager, "get") as mock_get:
        finder._fetch_cover_art("release-123")
        mock_get.assert_called_once()
        request = mock_get.call_args[0][0]
        url = request.url().toString()
        assert "coverartarchive.org/release/release-123" in url
        assert request.rawHeader("Accept") == b"application/json"


def test_handle_cover_art_reply_success_front_image(finder, qtbot):
    """Test _handle_cover_art_reply with successful JSON containing front image."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = json.dumps(
        {
            "images": [
                {"front": True, "image": "https://example.com/front.jpg"},
                {"front": False, "image": "https://example.com/back.jpg"},
            ]
        }
    ).encode("utf-8")

    with patch.object(finder, "_download_image") as mock_download:
        finder._handle_cover_art_reply(mock_reply)
        mock_download.assert_called_once_with("https://example.com/front.jpg")


def test_handle_cover_art_reply_no_front_falls_back(finder):
    """Test _handle_cover_art_reply uses first image if no front image."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = json.dumps(
        {
            "images": [
                {"front": False, "image": "https://example.com/back.jpg"},
                {"front": False, "image": "https://example.com/other.jpg"},
            ]
        }
    ).encode("utf-8")

    with patch.object(finder, "_download_image") as mock_download:
        finder._handle_cover_art_reply(mock_reply)
        mock_download.assert_called_once_with("https://example.com/back.jpg")


def test_handle_cover_art_reply_no_images(finder, qtbot):
    """Test _handle_cover_art_reply with no images emits error."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = json.dumps(
        {"images": []}
    ).encode("utf-8")

    with qtbot.wait_signal(finder.fetch_error) as blocker:
        finder._handle_cover_art_reply(mock_reply)
    error_msg = blocker.args[0]
    assert "No cover art found" in error_msg


def test_handle_cover_art_reply_network_error(finder, qtbot):
    """Test _handle_cover_art_reply with network error emits error."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.ConnectionRefusedError
    mock_reply.errorString.return_value = "Connection refused"

    with qtbot.wait_signal(finder.fetch_error) as blocker:
        finder._handle_cover_art_reply(mock_reply)
    error_msg = blocker.args[0]
    assert "Cover Art Archive request failed" in error_msg


def test_handle_cover_art_reply_json_decode_error(finder, qtbot):
    """Test _handle_cover_art_reply with invalid JSON emits error."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = b"invalid json"

    with qtbot.wait_signal(finder.fetch_error) as blocker:
        finder._handle_cover_art_reply(mock_reply)
    error_msg = blocker.args[0]
    assert "Failed to parse Cover Art Archive JSON" in error_msg


def test_download_image_constructs_request(finder):
    """Test _download_image constructs correct request."""
    with patch.object(QNetworkAccessManager, "get") as mock_get:
        finder._download_image("https://example.com/image.jpg")
        mock_get.assert_called_once()
        request = mock_get.call_args[0][0]
        url = request.url().toString()
        assert "example.com/image.jpg" in url
        assert (
            request.rawHeader("User-Agent")
            == b"MetaTag/1.0 (https://github.com/metatag)"
        )


def test_handle_image_reply_success(finder, qtbot):
    """Test _handle_image_reply with successful image data emits cover_fetched."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    # Create a tiny valid PNG using PIL
    from PIL import Image

    pil_img = Image.new("RGB", (10, 10), color="red")
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    png_data = buffer.getvalue()
    mock_reply.readAll.return_value.data.return_value = png_data

    with qtbot.wait_signal(finder.cover_fetched) as blocker:
        finder._handle_image_reply(mock_reply)
    emitted_image = blocker.args[0]
    assert isinstance(emitted_image, QImage)
    assert emitted_image.width() == 10
    assert emitted_image.height() == 10


def test_handle_image_reply_network_error(finder, qtbot):
    """Test _handle_image_reply with network error emits error."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.ConnectionRefusedError
    mock_reply.errorString.return_value = "Connection refused"

    with qtbot.wait_signal(finder.fetch_error) as blocker:
        finder._handle_image_reply(mock_reply)
    error_msg = blocker.args[0]
    assert "Image download failed" in error_msg


def test_handle_image_reply_empty_data(finder, qtbot):
    """Test _handle_image_reply with empty data emits error."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = b""

    with qtbot.wait_signal(finder.fetch_error) as blocker:
        finder._handle_image_reply(mock_reply)
    error_msg = blocker.args[0]
    assert "Empty image data" in error_msg


def test_handle_image_reply_load_fails(finder, qtbot):
    """Test _handle_image_reply when QImage.loadFromData fails."""
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = b"not an image"

    with qtbot.wait_signal(finder.fetch_error) as blocker:
        finder._handle_image_reply(mock_reply)
    error_msg = blocker.args[0]
    assert "Failed to load image data" in error_msg


def test_qimage_to_pil(finder):
    """Test qimage_to_pil converts QImage to PIL Image."""
    qimage = QImage(20, 30, QImage.Format.Format_ARGB32)
    qimage.fill(0xFFFF0000)  # Red
    pil_image = finder.qimage_to_pil(qimage)
    assert isinstance(pil_image, Image.Image)
    assert pil_image.size == (20, 30)
    # Check that conversion preserved something (PNG roundtrip)
    # The exact pixel values may differ due to format conversion
    # but ensure image is not empty
    assert pil_image.mode == "RGBA" or pil_image.mode == "RGB"


if __name__ == "__main__":
    pytest.main([__file__])
