"""Regex utilities for find and replace."""

import re
from typing import List


def find_matches(pattern: str, text: str) -> List[str]:
    """Find all matches of regex pattern in text."""
    try:
        matches = re.findall(pattern, text)
        return matches
    except re.error:
        return []


def replace_matches(pattern: str, replacement: str, text: str) -> str:
    """Replace all matches of regex pattern with replacement."""
    try:
        return re.sub(pattern, replacement, text)
    except re.error:
        return text


def apply_regex_to_fields(
    fields: dict[str, str],
    pattern: str,
    replacement: str,
    field_names: list[str],
    case_sensitive: bool = True,
) -> dict[str, str]:
    """Apply regex replacement to specified fields."""
    flags = 0 if case_sensitive else re.IGNORECASE
    result = fields.copy()
    for name in field_names:
        if name in result:
            try:
                result[name] = re.sub(pattern, replacement, result[name], flags=flags)
            except re.error:
                pass
    return result
