"""Unit tests for pattern engine (metatag.utils.patterns)."""

import pytest
from metatag.utils.patterns import (
    pattern_to_regex,
    validate_pattern,
    parse_filename,
    format_filename,
)


def test_pattern_to_regex_basic():
    regex = pattern_to_regex("%artist% - %title%")
    assert regex.startswith("^")
    assert regex.endswith("$")
    assert "(?P<artist>.+)" in regex
    assert "(?P<title>.+)" in regex


def test_pattern_to_regex_duplicate_placeholder():
    """Verify %artist%-%artist% does not raise re.error for duplicate group names."""
    regex = pattern_to_regex("%artist% - %artist%")
    assert "(?P<artist>.+)" in regex
    assert "(?P=artist)" in regex

    # Check parsing with backreference
    parsed = parse_filename("Queen - Queen", "%artist% - %artist%")
    assert parsed.get("artist") == "Queen"

    # Mismatched duplicates should not match
    mismatched = parse_filename("Queen - Bowie", "%artist% - %artist%")
    assert mismatched == {}


def test_validate_pattern():
    valid, err = validate_pattern("%artist% - %title%")
    assert valid is True
    assert err == ""

    # Duplicate placeholder is valid
    valid_dup, err_dup = validate_pattern("%artist% - %artist%")
    assert valid_dup is True
    assert err_dup == ""

    # Empty pattern
    invalid_empty, err_empty = validate_pattern("")
    assert invalid_empty is False
    assert "empty" in err_empty.lower()


def test_parse_filename_numeric():
    parsed = parse_filename("05 - Bohemian Rhapsody", "%track% - %title%")
    assert parsed.get("track_number") == "05"
    assert parsed.get("title") == "Bohemian Rhapsody"


def test_format_filename_all_fields():
    tags = {
        "artist": "Queen",
        "album": "A Night at the Opera",
        "title": "Bohemian Rhapsody",
        "track_number": 4,
        "disc_number": 1,
        "year": 1975,
        "genre": "Rock",
        "composer": "Freddie Mercury",
        "comment": "Masterpiece",
        "grouping": "Suite",
        "bpm": 120,
    }
    pattern = "%track2% - %artist% - %title% [%year%] (%genre%, by %composer%)"
    formatted = format_filename(tags, pattern)
    assert formatted == "04 - Queen - Bohemian Rhapsody [1975] (Rock, by Freddie Mercury)"


def test_format_filename_windows_reserved_names():
    """Verify that Windows reserved device names are sanitized to prevent filesystem issues."""
    tags = {
        "artist": "CON",
        "title": "Song",
    }
    # Pattern where output is just the reserved name
    formatted = format_filename(tags, "%artist%")
    assert formatted == "_CON"

    tags_aux = {"title": "AUX"}
    formatted_aux = format_filename(tags_aux, "%title%")
    assert formatted_aux == "_AUX"


def test_format_filename_illegal_characters():
    tags = {
        "artist": "AC/DC",
        "title": "What: Why? *Awesome*",
    }
    formatted = format_filename(tags, "%artist% - %title%")
    assert "/" not in formatted
    assert "?" not in formatted
    assert "*" not in formatted
