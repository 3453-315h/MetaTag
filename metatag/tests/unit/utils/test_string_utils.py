"""Unit tests for string_utils."""

import pytest
from metatag.utils.string_utils import (
    to_title_case,
    to_sentence_case,
    to_upper,
    to_lower,
)


def test_to_title_case_basic():
    """Test basic title case conversion."""
    assert to_title_case("hello world") == "Hello World"
    assert to_title_case("HELLO WORLD") == "Hello World"
    assert to_title_case("hElLo wOrLd") == "Hello World"


def test_to_title_case_empty():
    """Test title case with empty string."""
    assert to_title_case("") == ""


def test_to_title_case_single_word():
    """Test title case with single word."""
    assert to_title_case("hello") == "Hello"
    assert to_title_case("HELLO") == "Hello"
    assert to_title_case("h") == "H"


def test_to_title_case_multiple_spaces():
    """Test title case with multiple spaces."""
    # split() collapses whitespace
    assert to_title_case("hello   world") == "Hello World"
    assert to_title_case("  hello  world  ") == "Hello World"


def test_to_sentence_case_basic():
    """Test basic sentence case conversion."""
    assert to_sentence_case("hello world") == "Hello world"
    assert to_sentence_case("HELLO WORLD") == "HELLO WORLD"  # Only first char
    assert to_sentence_case("hElLo wOrLd") == "HElLo wOrLd"  # Only first char


def test_to_sentence_case_empty():
    """Test sentence case with empty string."""
    assert to_sentence_case("") == ""


def test_to_sentence_case_single_character():
    """Test sentence case with single character."""
    assert to_sentence_case("a") == "A"
    assert to_sentence_case("A") == "A"


def test_to_upper_basic():
    """Test uppercase conversion."""
    assert to_upper("hello") == "HELLO"
    assert to_upper("Hello World") == "HELLO WORLD"
    assert to_upper("123") == "123"


def test_to_upper_empty():
    """Test uppercase with empty string."""
    assert to_upper("") == ""


def test_to_lower_basic():
    """Test lowercase conversion."""
    assert to_lower("HELLO") == "hello"
    assert to_lower("Hello World") == "hello world"
    assert to_lower("123") == "123"


def test_to_lower_empty():
    """Test lowercase with empty string."""
    assert to_lower("") == ""


if __name__ == "__main__":
    pytest.main([__file__])
