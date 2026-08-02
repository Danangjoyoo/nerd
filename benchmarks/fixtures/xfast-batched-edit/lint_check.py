from pathlib import Path
import sys


def main(paths: list[str]) -> int:
    for value in paths:
        body = Path(value).read_text(encoding="utf-8")
        if "\t" in body or any(line.endswith(" ") for line in body.splitlines()):
            return 1
        if not body.endswith("\n"):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
