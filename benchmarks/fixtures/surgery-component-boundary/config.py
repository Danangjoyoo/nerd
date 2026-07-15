import os


def timeout_seconds() -> int:
    return os.getenv("TIMEOUT_SECONDS", "5")
