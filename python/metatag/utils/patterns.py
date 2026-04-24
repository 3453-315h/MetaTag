"""Pattern engine for MetaTag Pro automation."""

import re
from typing import Any, Dict, Optional, List

# Placeholders supported by the pattern engine
PLACEHOLDERS = {
    "%artist%": "artist",
    "%album%": "album",
    "%title%": "title",
    "%track%": "track_number",
    "%disc%": "disc_number",
    "%year%": "year",
    "%genre%": "genre",
    "%composer%": "composer",
}

def pattern_to_regex(pattern: str) -> str:
    """Convert a pattern like '%artist% - %title%' into a regex string."""
    # Escapes special characters except placeholders
    regex = re.escape(pattern)
    
    # Replace escaped placeholders with named regex groups
    # Note: we use (.+) for text and (\d+) for numbers
    for placeholder, attr in PLACEHOLDERS.items():
        escaped_p = re.escape(placeholder)
        if attr in ("track_number", "disc_number", "year"):
            # Numeric groups
            sub = f"(?P<{attr}>\\d+)"
        else:
            # Greedy text groups
            sub = f"(?P<{attr}>.+)"
        
        regex = regex.replace(escaped_p, sub)
    
    # Anchor to start and end
    return f"^{regex}$"

def parse_filename(filename: str, pattern: str) -> Dict[str, str]:
    """Extract metadata from a filename using a pattern."""
    regex_str = pattern_to_regex(pattern)
    match = re.search(regex_str, filename, re.IGNORECASE)
    if not match:
        return {}
    
    return {k: v for k, v in match.groupdict().items() if v}

def format_filename(tags: Dict[str, Any], pattern: str) -> str:
    """Construct a filename from tags using a pattern."""
    result = pattern
    for placeholder, attr in PLACEHOLDERS.items():
        val = tags.get(attr, "")
        if attr in ("track_number", "disc_number") and val:
            # Pad numbers (01, 02...)
            try:
                val = f"{int(val):02d}"
            except (ValueError, TypeError):
                pass
        
        # Sanitize the value: remove/replace characters that are invalid in filenames
        # or that could act as path separators.
        safe_val = re.sub(r'[\\/:*?"<>|]', '_', str(val))
        result = result.replace(placeholder, safe_val)
    return result
