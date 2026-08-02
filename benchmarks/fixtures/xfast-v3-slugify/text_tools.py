import re


def clean_text(value: str) -> str:
    """Return lowercase text with surrounding whitespace removed."""
    return value.strip().lower()


def slugify(value: str) -> str:
    raise NotImplementedError
