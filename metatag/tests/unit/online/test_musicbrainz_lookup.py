"""Unit tests for MusicBrainz lookup."""

import pytest
import json
from unittest.mock import Mock, patch
from PySide6.QtCore import QUrl, QUrlQuery
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from metatag.online.musicbrainz_lookup import MusicBrainzLookup


@pytest.fixture
def lookup():
    """Create a MusicBrainzLookup instance."""
    return MusicBrainzLookup()


def test_initialization(lookup):
    """Test MusicBrainzLookup can be instantiated."""
    assert lookup is not None
    assert isinstance(lookup._nam, QNetworkAccessManager)


def test_lookup_release_empty_artist_album(lookup, qtbot):
    """Test lookup with empty artist and album emits error."""
    with qtbot.wait_signal(lookup.lookup_error) as blocker:
        lookup.lookup_release("", "")

    error_msg = blocker.args[0]
    assert "cannot both be empty" in error_msg


def test_lookup_release_constructs_url():
    """Test that lookup_release constructs correct URL."""
    lookup = MusicBrainzLookup()
    with patch.object(QNetworkAccessManager, "get") as mock_get:
        lookup.lookup_release("Test Artist", "Test Album")
        mock_get.assert_called_once()
        request = mock_get.call_args[0][0]
        url = request.url().toString()
        assert "musicbrainz.org" in url
        assert "artist" in url
        assert "release" in url


def test_handle_reply_finished_success():
    """Test _handle_reply_finished with successful response."""
    lookup = MusicBrainzLookup()
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = json.dumps(
        {"releases": [{"id": "123"}, {"id": "456"}]}
    ).encode("utf-8")

    # Capture emitted signal
    captured_ids = []

    def capture(ids):
        captured_ids.extend(ids)

    lookup.releases_fetched.connect(capture)

    lookup._handle_reply_finished(mock_reply)

    assert captured_ids == ["123", "456"]


def test_handle_reply_finished_no_releases():
    """Test _handle_reply_finished when no releases found."""
    lookup = MusicBrainzLookup()
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = json.dumps(
        {"releases": []}
    ).encode("utf-8")

    captured_error = []

    def capture(err):
        captured_error.append(err)

    lookup.lookup_error.connect(capture)

    lookup._handle_reply_finished(mock_reply)

    assert len(captured_error) == 1
    assert "No releases found" in captured_error[0]


def test_handle_reply_finished_network_error():
    """Test _handle_reply_finished with network error."""
    lookup = MusicBrainzLookup()
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.ConnectionRefusedError
    mock_reply.errorString.return_value = "Connection refused"

    captured_error = []
    lookup.lookup_error.connect(captured_error.append)

    lookup._handle_reply_finished(mock_reply)

    assert len(captured_error) == 1
    assert "Connection refused" in captured_error[0]


def test_handle_reply_finished_json_decode_error():
    """Test _handle_reply_finished with invalid JSON."""
    lookup = MusicBrainzLookup()
    mock_reply = Mock(spec=QNetworkReply)
    mock_reply.error.return_value = QNetworkReply.NetworkError.NoError
    mock_reply.readAll.return_value.data.return_value = b"invalid json"

    captured_error = []
    lookup.lookup_error.connect(captured_error.append)

    lookup._handle_reply_finished(mock_reply)

    assert len(captured_error) == 1
    assert "Failed to parse" in captured_error[0]


def test_handle_ssl_errors_ignorable():
    """Test _handle_ssl_errors with ignorable errors."""
    lookup = MusicBrainzLookup()
    mock_sender = Mock()
    mock_sender.ignoreSslErrors = Mock()

    # Mock QSslError
    from PySide6.QtNetwork import QSslError

    mock_error = Mock(spec=QSslError)
    mock_error.error.return_value = QSslError.SslError.SelfSignedCertificate

    with patch.object(lookup, "sender", return_value=mock_sender):
        lookup._handle_ssl_errors([mock_error])

        mock_sender.ignoreSslErrors.assert_called_once_with([mock_error])


def test_handle_ssl_errors_non_ignorable():
    """Test _handle_ssl_errors with non-ignorable errors."""
    lookup = MusicBrainzLookup()
    mock_sender = Mock()
    mock_sender.ignoreSslErrors = Mock()

    from PySide6.QtNetwork import QSslError

    mock_error = Mock(spec=QSslError)
    mock_error.error.return_value = QSslError.SslError.CertificateRevoked

    with patch.object(lookup, "sender", return_value=mock_sender):
        lookup._handle_ssl_errors([mock_error])

        # Should not call ignoreSslErrors because error is not ignorable
        mock_sender.ignoreSslErrors.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
