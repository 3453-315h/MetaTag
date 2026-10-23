"""Pattern engine for MetaTag Pro automation."""

import re
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

from .rename_utils import sanitize_filename

# Placeholders supported by the pattern engine
PLACEHOLDERS = {
    "%artist%": "artist",
    "%album%": "album",
    "%title%": "title",
    "%track%": "track_number",
    "%track2%": "track_number",
    "%track3%": "track_number",
    "%disc%": "disc_number",
    "%year%": "year",
    "%genre%": "genre",
    "%composer%": "composer",
    "%comment%": "comment",
    "%grouping%": "grouping",
    "%bpm%": "bpm",
}


def pattern_to_regex(pattern: str) -> str:
    """Convert a pattern like '%artist% - %title%' into a regex string.
    
    If a placeholder appears multiple times (e.g. '%artist% - %artist%'),
    the first occurrence creates a named group and subsequent occurrences
    use backreferences to prevent re.error for duplicate group names.
    """
    regex = re.escape(pattern)
    seen_attrs = set()
    
    # Sort placeholders by length descending so %track2% is replaced before %track%
    sorted_placeholders = sorted(PLACEHOLDERS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for placeholder, attr in sorted_placeholders:
        escaped_p = re.escape(placeholder)
        if escaped_p in regex:
            parts = regex.split(escaped_p)
            new_regex = parts[0]
            for part in parts[1:]:
                if attr not in seen_attrs:
                    if attr in ("track_number", "disc_number", "year", "bpm"):
                        sub = f"(?P<{attr}>\\d+)"
                    else:
                        sub = f"(?P<{attr}>.+)"
                    seen_attrs.add(attr)
                else:
                    sub = f"(?P={attr})"
                new_regex += sub + part
            regex = new_regex
            
    return f"^{regex}$"


def validate_pattern(pattern: str) -> Tuple[bool, str]:
    """Validate if pattern can be converted to a valid regex."""
    if not pattern:
        return False, "Pattern cannot be empty"
    try:
        regex_str = pattern_to_regex(pattern)
        re.compile(regex_str)
        return True, ""
    except Exception as e:
        return False, str(e)


def parse_filename(filename: str, pattern: str) -> Dict[str, str]:
    """Extract metadata from a filename using a pattern."""
    try:
        regex_str = pattern_to_regex(pattern)
        match = re.search(regex_str, filename, re.IGNORECASE)
        if not match:
            return {}
        return {k: v for k, v in match.groupdict().items() if v}
    except Exception:
        return {}


def format_filename(tags: Dict[str, Any], pattern: str) -> str:
    """Construct a sanitized filename from tags using a pattern."""
    result = pattern
    sorted_placeholders = sorted(PLACEHOLDERS.items(), key=lambda x: len(x[0]), reverse=True)
    for placeholder, attr in sorted_placeholders:
        if placeholder not in result:
            continue
        val = tags.get(attr, "")
        if val is None:
            val = ""
        if placeholder == "%track2%":
            try:
                val = f"{int(val):02d}" if int(val) > 0 else ""
            except (ValueError, TypeError):
                pass
        elif placeholder == "%track3%":
            try:
                val = f"{int(val):03d}" if int(val) > 0 else ""
            except (ValueError, TypeError):
                pass
        elif attr in ("track_number", "disc_number") and val:
            try:
                val = f"{int(val):02d}" if int(val) > 0 else ""
            except (ValueError, TypeError):
                pass
        # Sanitize tag value: replace path separators and illegal chars with '_'
        safe_val = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', str(val))
        result = result.replace(placeholder, safe_val)

    # Sanitize each path component separately so sub-directories survive
    parts = Path(result).parts
    sanitized = Path(*[sanitize_filename(p) for p in parts]) if parts else Path("_")
    return str(sanitized)
