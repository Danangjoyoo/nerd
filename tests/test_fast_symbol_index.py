from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "nerd-fast" / "scripts" / "symbol_index.py"


def load_indexer():
    spec = importlib.util.spec_from_file_location("nerd_fast_symbol_index", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CacheContractTests(unittest.TestCase):
    def test_cache_is_outside_workspace_and_stable_for_canonical_root(self):
        indexer = load_indexer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            root.mkdir()
            first = indexer.default_cache_path(root)
            second = indexer.default_cache_path(root / ".")
            self.assertEqual(first, second)
            self.assertFalse(first.is_relative_to(root))
            self.assertEqual(first.name, "index.sqlite3")

    def test_replace_is_idempotent_and_find_is_exact(self):
        indexer = load_indexer()
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "index.sqlite3"
            connection = indexer.connect_cache(cache)
            indexer.initialize_schema(connection, Path(directory))
            symbols = [
                {
                    "name": "Widget",
                    "path": "src/widget.py",
                    "line": 7,
                    "kind": "class",
                    "scope": None,
                    "language": "Python",
                    "signature": None,
                }
            ]
            indexer.replace_file_symbols(
                connection,
                "src/widget.py",
                indexer.FileFingerprint(mtime_ns=10, size=20),
                symbols,
            )
            indexer.replace_file_symbols(
                connection,
                "src/widget.py",
                indexer.FileFingerprint(mtime_ns=10, size=20),
                symbols,
            )
            self.assertEqual(indexer.find_symbol(connection, "Widget"), symbols)
            self.assertEqual(indexer.find_symbol(connection, "Wid"), [])
            connection.close()


class CtagsContractTests(unittest.TestCase):
    def test_rejects_non_universal_or_non_json_ctags(self):
        indexer = load_indexer()

        def bsd_runner(*args, **kwargs):
            return indexer.subprocess.CompletedProcess(
                args[0], 0, stdout="Exuberant Ctags 5.8\n", stderr=""
            )

        with self.assertRaisesRegex(RuntimeError, "Universal Ctags"):
            indexer.require_universal_ctags("ctags", runner=bsd_runner)

        calls = iter(
            (
                indexer.subprocess.CompletedProcess(
                    ["ctags", "--version"],
                    0,
                    stdout="Universal Ctags 6.2.0\n",
                    stderr="",
                ),
                indexer.subprocess.CompletedProcess(
                    ["ctags", "--list-features"],
                    0,
                    stdout="wildcards\n",
                    stderr="",
                ),
            )
        )
        with self.assertRaisesRegex(RuntimeError, "JSON"):
            indexer.require_universal_ctags(
                "ctags", runner=lambda *args, **kwargs: next(calls)
            )

    def test_accepts_tabular_universal_ctags_features(self):
        indexer = load_indexer()
        calls = iter(
            (
                indexer.subprocess.CompletedProcess(
                    ["ctags", "--version"],
                    0,
                    stdout="Universal Ctags 6.2.1\n",
                    stderr="",
                ),
                indexer.subprocess.CompletedProcess(
                    ["ctags", "--list-features"],
                    0,
                    stdout=(
                        "#NAME                       DESCRIPTION\n"
                        "wildcards                   can use glob matching\n"
                        "json                        supports json format output\n"
                    ),
                    stderr="",
                ),
            )
        )

        indexer.require_universal_ctags(
            "ctags", runner=lambda *args, **kwargs: next(calls)
        )

    def test_parses_only_tag_records_and_normalizes_paths(self):
        indexer = load_indexer()
        lines = [
            '{"_type":"ptag","name":"JSON_OUTPUT_VERSION","path":"1.0"}\n',
            '{"_type":"tag","name":"Widget","path":"src/widget.py",'
            '"line":7,"kind":"class","language":"Python"}\n',
        ]
        parsed = indexer.parse_ctags_json(lines, Path("/workspace"))
        self.assertEqual(
            parsed,
            [
                {
                    "name": "Widget",
                    "path": "src/widget.py",
                    "line": 7,
                    "kind": "class",
                    "scope": None,
                    "language": "Python",
                    "signature": None,
                }
            ],
        )

    def test_json_generation_requests_line_numbers_without_patterns(self):
        indexer = load_indexer()
        commands: list[list[str]] = []

        class Output:
            def __iter__(self):
                return iter(())

            def close(self):
                return None

        class Process:
            stdout = Output()

            def wait(self):
                return 0

        def popen(command, **kwargs):
            commands.append(command)
            return Process()

        original = indexer.subprocess.Popen
        indexer.subprocess.Popen = popen
        try:
            indexer.generate_tags("ctags", Path("/workspace"), ["widget.py"])
        finally:
            indexer.subprocess.Popen = original

        self.assertIn("--fields=+nsS-P", commands[0])
        self.assertNotIn("--excmd=number", commands[0])

    def test_large_generation_uses_one_line_list_process(self):
        indexer = load_indexer()
        commands: list[list[str]] = []
        inputs: list[str | None] = []

        class Output:
            def __iter__(self):
                return iter(())

            def close(self):
                return None

        class Process:
            stdout = Output()

            def wait(self):
                return 0

        def popen(command, **kwargs):
            commands.append(command)
            stream = kwargs.get("stdin")
            inputs.append(stream.read() if stream is not None else None)
            return Process()

        paths = [f"src/module_{index}.py" for index in range(201)]
        original = indexer.subprocess.Popen
        indexer.subprocess.Popen = popen
        try:
            indexer.generate_tags("ctags", Path("/workspace"), paths[:200])
            self.assertEqual(len(commands), 1)
            self.assertNotIn("-L", commands[0])
            self.assertIsNone(inputs[0])
            commands.clear()
            inputs.clear()
            indexer.generate_tags("ctags", Path("/workspace"), paths)
        finally:
            indexer.subprocess.Popen = original

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0][-2:], ["-L", "-"])
        self.assertEqual(inputs[0].splitlines()[0], "./src/module_0.py")
        self.assertEqual(len(inputs[0].splitlines()), 201)

    def test_line_unsafe_paths_fall_back_to_argument_batches(self):
        indexer = load_indexer()

        class Output:
            def __iter__(self):
                return iter(())

            def close(self):
                return None

        class Process:
            stdout = Output()

            def wait(self):
                return 0

        for unsafe in ("odd\nname.py", "trailing.py "):
            with self.subTest(path=unsafe):
                commands: list[list[str]] = []

                def popen(command, **kwargs):
                    commands.append(command)
                    return Process()

                paths = [f"src/module_{index}.py" for index in range(200)]
                paths.append(unsafe)
                original = indexer.subprocess.Popen
                indexer.subprocess.Popen = popen
                try:
                    indexer.generate_tags("ctags", Path("/workspace"), paths)
                finally:
                    indexer.subprocess.Popen = original

                self.assertEqual(len(commands), 2)
                self.assertTrue(all("-L" not in command for command in commands))
                self.assertIn(f"./{unsafe}", commands[-1])


class RefreshContractTests(unittest.TestCase):
    def test_refresh_indexes_only_changes_and_removes_deleted_files(self):
        indexer = load_indexer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            root.mkdir()
            source = root / "widget.py"
            source.write_text("class Widget:\n    pass\n", encoding="utf-8")
            cache = Path(directory) / "cache" / "index.sqlite3"
            connection = indexer.connect_cache(cache)
            indexer.initialize_schema(connection, root)
            calls: list[list[str]] = []

            def tags(paths: list[str]):
                calls.append(paths)
                return [
                    {
                        "name": "Widget",
                        "path": "widget.py",
                        "line": 1,
                        "kind": "class",
                        "scope": None,
                        "language": "Python",
                        "signature": None,
                    }
                ]

            first = indexer.refresh_index(
                connection,
                root,
                tags,
                files=["widget.py"],
            )
            second = indexer.refresh_index(
                connection,
                root,
                tags,
                files=["widget.py"],
            )
            source.unlink()
            third = indexer.refresh_index(connection, root, tags, files=[])

            self.assertEqual(calls, [["widget.py"]])
            self.assertEqual(first, {"changed": 1, "removed": 0})
            self.assertEqual(second, {"changed": 0, "removed": 0})
            self.assertEqual(third, {"changed": 0, "removed": 1})
            self.assertEqual(indexer.find_symbol(connection, "Widget"), [])
            connection.close()


class CliContractTests(unittest.TestCase):
    def test_find_reads_existing_cache_without_refreshing(self):
        indexer = load_indexer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            root.mkdir()
            cache = Path(directory) / "index.sqlite3"
            connection = indexer.connect_cache(cache)
            indexer.initialize_schema(connection, root)
            indexer.replace_file_symbols(
                connection,
                "widget.py",
                indexer.FileFingerprint(1, 1),
                [
                    {
                        "name": "Widget",
                        "path": "widget.py",
                        "line": 1,
                        "kind": "class",
                        "scope": None,
                        "language": "Python",
                        "signature": None,
                    }
                ],
            )
            connection.close()
            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "find",
                    "Widget",
                    "--root",
                    str(root),
                    "--cache",
                    str(cache),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(json.loads(result.stdout)["matches"][0]["line"], 1)

    def test_ensure_reports_unavailable_ctags_without_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "ensure",
                    "--root",
                    directory,
                    "--ctags",
                    "definitely-missing-universal-ctags",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Universal Ctags", result.stderr)


if __name__ == "__main__":
    unittest.main()
