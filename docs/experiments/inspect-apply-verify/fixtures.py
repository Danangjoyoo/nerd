from __future__ import annotations

import difflib
import hashlib
from pathlib import Path
import shutil


SMALL_BEFORE = {
    "feature.py": "def greet(name):\n    return name\n",
    "test_feature.py": (
        "import unittest\n\n"
        "from feature import greet\n\n\n"
        "class FeatureTests(unittest.TestCase):\n"
        "    def test_greet(self):\n"
        "        self.assertEqual(greet('Ada'), 'Hello, Ada!')\n\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    ),
}

SMALL_AFTER = {
    **SMALL_BEFORE,
    "feature.py": "def greet(name):\n    return f\"Hello, {name}!\"\n",
}

LARGE_BEFORE = {
    "alpha.py": "def identity(value):\n    return value\n",
    "beta.py": "def identity_label(value):\n    return str(value)\n",
    "test_math_ops.py": (
        "import unittest\n\n"
        "from alpha import identity\n"
        "from beta import identity_label\n\n\n"
        "class MathTests(unittest.TestCase):\n"
        "    def test_existing_behavior(self):\n"
        "        self.assertEqual(identity(3), 3)\n"
        "        self.assertEqual(identity_label(3), '3')\n\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    ),
    "lint_check.py": (
        "from pathlib import Path\n"
        "import sys\n\n\n"
        "for value in sys.argv[1:]:\n"
        "    text = Path(value).read_text(encoding='utf-8')\n"
        "    if '\\t' in text or not text.endswith('\\n'):\n"
        "        raise SystemExit(1)\n"
    ),
}

LARGE_AFTER = {
    **LARGE_BEFORE,
    "alpha.py": (
        "def identity(value):\n"
        "    return value\n\n\n"
        "def clamp(value, minimum, maximum):\n"
        "    return max(minimum, min(maximum, value))\n"
    ),
    "beta.py": (
        "def identity_label(value):\n"
        "    return str(value)\n\n\n"
        "def parity_label(value):\n"
        "    return 'even' if value % 2 == 0 else 'odd'\n"
    ),
    "test_math_ops.py": (
        "import unittest\n\n"
        "from alpha import clamp, identity\n"
        "from beta import identity_label, parity_label\n\n\n"
        "class MathTests(unittest.TestCase):\n"
        "    def test_existing_behavior(self):\n"
        "        self.assertEqual(identity(3), 3)\n"
        "        self.assertEqual(identity_label(3), '3')\n\n"
        "    def test_clamp(self):\n"
        "        self.assertEqual(clamp(8, 0, 5), 5)\n"
        "        self.assertEqual(clamp(-2, 0, 5), 0)\n\n"
        "    def test_parity_label(self):\n"
        "        self.assertEqual(parity_label(4), 'even')\n"
        "        self.assertEqual(parity_label(3), 'odd')\n\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    ),
}

APPLY_CASES = {
    "apply-small": {
        "before": SMALL_BEFORE,
        "after": SMALL_AFTER,
        "checks": [["python3", "-m", "unittest", "-q", "test_feature.py"]],
    },
    "apply-large": {
        "before": LARGE_BEFORE,
        "after": LARGE_AFTER,
        "checks": [
            [
                "python3",
                "-m",
                "py_compile",
                "alpha.py",
                "beta.py",
                "test_math_ops.py",
            ],
            [
                "python3",
                "lint_check.py",
                "alpha.py",
                "beta.py",
                "test_math_ops.py",
            ],
            ["python3", "-m", "unittest", "-q", "test_math_ops.py"],
        ],
    },
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative.startswith("__pycache__/") or "/__pycache__/" in relative:
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _replace_root(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)


def _write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def materialize(case_id: str, root: Path) -> None:
    _replace_root(root)
    if case_id == "inspect-small":
        lines = [f"value_{index} = {index}\n" for index in range(200)]
        lines[99] = "def target_small(value):\n"
        lines[100] = "    return value + 1\n"
        _write_files(root, {"small.py": "".join(lines)})
        return
    if case_id == "inspect-large":
        for file_index in range(200):
            lines = [
                f"value_{file_index}_{line_index} = {line_index}\n"
                for line_index in range(250)
            ]
            if file_index in {17, 83, 161}:
                lines[120] = "def target_large(value):\n"
                lines[121] = "    return value * 2\n"
            _write_files(root, {f"module_{file_index:03d}.py": "".join(lines)})
        return
    try:
        case = APPLY_CASES[case_id]
    except KeyError as error:
        raise ValueError(f"unknown fixture case: {case_id}") from error
    _write_files(root, case["before"])


def patch_for(case_id: str) -> str:
    case = APPLY_CASES[case_id]
    chunks: list[str] = []
    for relative in sorted(case["after"]):
        before = case["before"][relative].splitlines(keepends=True)
        after = case["after"][relative].splitlines(keepends=True)
        if before == after:
            continue
        chunks.extend(
            difflib.unified_diff(
                before,
                after,
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
    return "".join(chunks)


def expected_hashes(case_id: str, root: Path) -> dict[str, str]:
    case = APPLY_CASES[case_id]
    return {
        relative: file_hash(root / relative)
        for relative in sorted(case["after"])
        if case["before"][relative] != case["after"][relative]
    }


def checks_for(case_id: str) -> list[list[str]]:
    return [list(command) for command in APPLY_CASES[case_id]["checks"]]
