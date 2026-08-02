import re


def normalize_slug(text: str) -> str:
    """Normalize text for use as a URL slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")


def normalize_label(text: str) -> str:
    """Normalize human-readable label whitespace."""
    return " ".join(text.strip().split())
