"""String utilities."""


def to_title_case(s: str) -> str:
    """Convert string to Title Case."""
    if not s:
        return s
    words = s.split()
    title_words = []
    for word in words:
        if word:
            title_words.append(word[0].upper() + word[1:].lower())
    return " ".join(title_words)


def to_sentence_case(s: str) -> str:
    """Convert string to Sentence case."""
    if not s:
        return s
    return s[0].upper() + s[1:]


def to_upper(s: str) -> str:
    """Convert string to uppercase."""
    return s.upper()


def to_lower(s: str) -> str:
    """Convert string to lowercase."""
    return s.lower()
