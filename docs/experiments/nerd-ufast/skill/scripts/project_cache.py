#!/usr/bin/env python3
"""Read and atomically update UFast's best-effort project cache."""

import argparse
import fcntl
import hashlib
import os
import re
import tempfile
from pathlib import Path


KEY_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*")
MARKER_PATTERN = re.compile(r"##@ ([a-z0-9][a-z0-9_-]*) @##")
CACHE_NAMES = (
    "project-map",
    "conventions",
    "commands",
    "dependencies",
    "history",
)


def parse_key(value):
    if not KEY_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "key must use lowercase letters, digits, hyphens, or underscores"
        )
    return value


def cache_root():
    override = os.environ.get("NERD_UFAST_CACHE_ROOT")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".agent" / "tmp" / "nerd-ufast"


def cache_path(repo, cache):
    root = Path(repo).resolve()
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", root.name).strip("-") or "project"
    digest = hashlib.sha256(str(root).encode()).hexdigest()[:12]
    return cache_root() / f"{slug}-{digest}" / f"{cache}.md"


def parse_cache(text):
    entries = {}
    key = None
    lines = []

    for line in text.splitlines():
        marker = MARKER_PATTERN.fullmatch(line)
        if marker:
            if key is not None:
                entries[key] = "\n".join(lines).strip()
            key = marker.group(1)
            lines = []
        elif key is not None:
            lines.append(line)

    if key is not None:
        entries[key] = "\n".join(lines).strip()
    return entries


def render_cache(entries):
    sections = [f"##@ {key} @##\n{entries[key].strip()}" for key in sorted(entries)]
    return "\n\n".join(sections) + "\n"


def read_key(repo, cache, key):
    path = cache_path(repo, cache)
    try:
        entries = parse_cache(path.read_text())
    except (OSError, UnicodeError):
        return None
    return entries.get(key)


def write_key(repo, cache, key, value):
    if any(MARKER_PATTERN.fullmatch(line) for line in value.splitlines()):
        raise ValueError("cache values cannot contain key markers")

    path = cache_path(repo, cache)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    temporary_path = None

    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            try:
                entries = parse_cache(path.read_text())
            except (OSError, UnicodeError):
                entries = {}
            entries[key] = value.strip()

            with tempfile.NamedTemporaryFile(
                "w",
                dir=path.parent,
                delete=False,
                encoding="utf-8",
            ) as temporary:
                temporary.write(render_cache(entries))
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            fcntl.flock(lock, fcntl.LOCK_UN)


def build_parser():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    get_parser = commands.add_parser("get")
    get_parser.add_argument("--repo", required=True)
    get_parser.add_argument("--cache", required=True, choices=CACHE_NAMES)
    get_parser.add_argument("--key", required=True, type=parse_key)

    put_parser = commands.add_parser("put")
    put_parser.add_argument("--repo", required=True)
    put_parser.add_argument("--cache", required=True, choices=CACHE_NAMES)
    put_parser.add_argument("--key", required=True, type=parse_key)
    put_parser.add_argument("--value", required=True)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "get":
        value = read_key(args.repo, args.cache, args.key)
        if value is None:
            return 1
        print(value)
        return 0

    try:
        write_key(args.repo, args.cache, args.key, args.value)
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
