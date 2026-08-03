from pathlib import Path
import sys


raise SystemExit(
    0
    if all(Path(path).read_text(encoding="utf-8").endswith("\n") for path in sys.argv[1:])
    else 1
)
