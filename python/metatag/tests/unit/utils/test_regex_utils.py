"""Unit tests for regex_utils."""

import pytest
from metatag.utils.regex_utils import (
    find_matches,
    replace_matches,
    apply_regex_to_fields,
)


def test_find_matches_basic():
    """Test basic pattern matching."""
    text = "hello world hello"
    pattern = r"hello"
    result = find_matches(pattern, text)
    assert result == ["hello", "hello"]


def test_find_matches_no_matches():
    """Test pattern with no matches."""
    text = "hello world"
    pattern = r"goodbye"
    result = find_matches(pattern, text)
    assert result == []


def test_find_matches_invalid_regex():
    """Test invalid regex pattern."""
    text = "hello world"
    pattern = r"["
    result = find_matches(pattern, text)
    assert result == []  # Should return empty list on error


def test_find_matches_groups():
    """Test pattern with capture groups."""
    text = "abc123 def456"
    pattern = r"([a-z]+)([0-9]+)"
    result = find_matches(pattern, text)
    # findall returns tuples for groups
    assert result == [("abc", "123"), ("def", "456")]


def test_replace_matches_basic():
    """Test basic replacement."""
    text = "hello world"
    pattern = r"world"
    replacement = "universe"
    result = replace_matches(pattern, replacement, text)
    assert result == "hello universe"


def test_replace_matches_multiple():
    """Test multiple replacements."""
    text = "a b a b a"
    pattern = r"a"
    replacement = "x"
    result = replace_matches(pattern, replacement, text)
    assert result == "x b x b x"


def test_replace_matches_invalid_regex():
    """Test invalid regex in replacement."""
    text = "hello world"
    pattern = r"["
    replacement = "x"
    result = replace_matches(pattern, replacement, text)
    assert result == text  # Should return original on error


def test_replace_matches_backreferences():
    """Test replacement with backreferences."""
    text = "hello world"
    pattern = r"(\w+) (\w+)"
    replacement = r"\2 \1"
    result = replace_matches(pattern, replacement, text)
    assert result == "world hello"


def test_apply_regex_to_fields_basic():
    """Test applying regex to specific fields."""
    fields = {"artist": "The Beatles", "title": "Hey Jude", "album": ""}
    pattern = r"The "
    replacement = ""
    field_names = ["artist"]
    result = apply_regex_to_fields(fields, pattern, replacement, field_names)
    assert result["artist"] == "Beatles"
    assert result["title"] == "Hey Jude"  # unchanged
    assert result["album"] == ""


def test_apply_regex_to_fields_multiple():
    """Test applying regex to multiple fields."""
    fields = {"artist": "The Who", "title": "The Real Me", "album": "Quadrophenia"}
    pattern = r"The "
    replacement = ""
    field_names = ["artist", "title", "album"]
    result = apply_regex_to_fields(fields, pattern, replacement, field_names)
    assert result["artist"] == "Who"
    assert result["title"] == "Real Me"
    assert result["album"] == "Quadrophenia"  # no "The" in this one


def test_apply_regex_to_fields_case_insensitive():
    """Test case-insensitive replacement."""
    fields = {"artist": "THE BEATLES", "title": "the end"}
    pattern = r"the"
    replacement = ""
    field_names = ["artist", "title"]
    result = apply_regex_to_fields(
        fields, pattern, replacement, field_names, case_sensitive=False
    )
    assert result["artist"] == " BEATLES"
    assert result["title"] == " end"


def test_apply_regex_to_fields_case_sensitive():
    """Test case-sensitive replacement."""
    fields = {"artist": "THE BEATLES", "title": "the end"}
    pattern = r"the"
    replacement = ""
    field_names = ["artist", "title"]
    result = apply_regex_to_fields(
        fields, pattern, replacement, field_names, case_sensitive=True
    )
    assert result["artist"] == "THE BEATLES"  # no match (uppercase)
    assert result["title"] == " end"  # match (lowercase)


def test_apply_regex_to_fields_invalid_regex():
    """Test invalid regex in field application."""
    fields = {"artist": "test"}
    pattern = r"["
    replacement = "x"
    field_names = ["artist"]
    result = apply_regex_to_fields(fields, pattern, replacement, field_names)
    # Should leave field unchanged on error
    assert result["artist"] == "test"


def test_apply_regex_to_fields_missing_field():
    """Test when field not in dictionary."""
    fields = {"artist": "test"}
    pattern = r"t"
    replacement = "x"
    field_names = ["artist", "nonexistent"]
    result = apply_regex_to_fields(fields, pattern, replacement, field_names)
    # Should only affect existing fields
    assert result["artist"] == "xesx"
    assert "nonexistent" not in result


if __name__ == "__main__":
    pytest.main([__file__])
