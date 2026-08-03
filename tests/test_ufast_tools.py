from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = (
    ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_core.py"
)
SERVER_PATH = (
    ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_mcp.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def digest(body: str) -> str:
    return hashlib.sha256(body.encode()).hexdigest()


def fixture(root: Path) -> None:
    (root / "feature.py").write_text(
        "def greet(name: str) -> str:\n    raise NotImplementedError\n",
        encoding="utf-8",
    )
    (root / "test_feature.py").write_text(
        "import unittest\n\n"
        "from feature import greet\n\n"
        "class FeatureTests(unittest.TestCase):\n"
        "    def test_greet(self):\n"
        "        self.assertEqual(greet('Ada'), 'Hello, Ada!')\n",
        encoding="utf-8",
    )
    (root / "lint_check.py").write_text(
        "from pathlib import Path\n"
        "import sys\n\n"
        "raise SystemExit(0 if all(Path(p).read_text().endswith('\\n') "
        "for p in sys.argv[1:]) else 1)\n",
        encoding="utf-8",
    )
    (root / "verify_behavior.py").write_text(
        "import unittest\n\n"
        "from feature import greet\n\n"
        "class BehaviorTests(unittest.TestCase):\n"
        "    def test_greet(self):\n"
        "        self.assertEqual(greet('Grace'), 'Hello, Grace!')\n",
        encoding="utf-8",
    )


class PrepareContractTests(unittest.TestCase):
    def test_returns_bounded_editable_context_hashes_and_check_capabilities(self):
        core = load_module("nerd_ufast_core_prepare", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            hidden = root / ".agents" / "skills"
            hidden.mkdir(parents=True)
            (hidden / "secret.py").write_text("TOKEN = 'hidden'\n")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "cache.py").write_text("hidden = True\n")

            result = core.prepare_workspace_change(root)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(
            [item["path"] for item in result["files"]],
            ["feature.py", "test_feature.py"],
        )
        self.assertEqual(
            result["files"][0]["sha256"],
            digest("def greet(name: str) -> str:\n    raise NotImplementedError\n"),
        )
        self.assertEqual(
            result["checks"],
            ["syntax", "fixture_lint", "changed_tests", "verify_behavior"],
        )
        self.assertGreaterEqual(result["operation_ms"], 0)

    def test_rejects_symlinks_and_excessive_context(self):
        core = load_module("nerd_ufast_core_prepare_limits", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.py"
            target.write_text("value = 1\n")
            (root / "linked.py").symlink_to(target)

            result = core.prepare_workspace_change(root)
            self.assertEqual(result["status"], "unsupported")
            self.assertIn("symlink", result["reason"])

            (root / "linked.py").unlink()
            for index in range(13):
                (root / f"module_{index}.py").write_text("value = 1\n")
            result = core.prepare_workspace_change(root)
            self.assertEqual(result["status"], "unsupported")
            self.assertIn("12", result["reason"])


class ApplyContractTests(unittest.TestCase):
    def test_applies_generic_text_and_structured_workspace_files(self):
        core = load_module("nerd_ufast_core_generic", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Before\n", encoding="utf-8")
            (root / "settings.json").write_text(
                '{"enabled": false}\n',
                encoding="utf-8",
            )
            (root / "asset.bin").write_bytes(b"\x00\xff\x10")
            prepared = core.prepare_workspace_change(root)
            self.assertEqual(
                [item["path"] for item in prepared["files"]],
                ["README.md", "settings.json"],
            )
            hashes = {item["path"]: item["sha256"] for item in prepared["files"]}

            result = core.apply_workspace_change(
                root,
                [
                    {
                        "path": "README.md",
                        "expected_sha256": hashes["README.md"],
                        "content": "# After\n",
                    },
                    {
                        "path": "settings.json",
                        "expected_sha256": hashes["settings.json"],
                        "content": '{"enabled": true}\n',
                    },
                ],
            )

            self.assertEqual(result["status"], "applied", result)
            self.assertEqual([check["name"] for check in result["checks"]], ["syntax"])
            self.assertEqual((root / "README.md").read_text(), "# After\n")
            self.assertEqual(json.loads((root / "settings.json").read_text()), {"enabled": True})

    def test_invalid_structured_text_is_rejected_before_writing(self):
        core = load_module("nerd_ufast_core_generic_invalid", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = '{"enabled": false}\n'
            path = root / "settings.json"
            path.write_text(original, encoding="utf-8")
            result = core.apply_workspace_change(
                root,
                [
                    {
                        "path": "settings.json",
                        "expected_sha256": digest(original),
                        "content": "{not valid json}\n",
                    }
                ],
            )

            self.assertEqual(result["status"], "verification_failed")
            self.assertFalse(result["rolled_back"])
            self.assertEqual(path.read_text(), original)

    def test_applies_complete_batch_and_runs_fixed_checks(self):
        core = load_module("nerd_ufast_core_apply", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            prepared = core.prepare_workspace_change(root)
            hashes = {item["path"]: item["sha256"] for item in prepared["files"]}
            result = core.apply_workspace_change(
                root,
                [
                    {
                        "path": "feature.py",
                        "expected_sha256": hashes["feature.py"],
                        "content": (
                            "def greet(name: str) -> str:\n"
                            "    return f'Hello, {name}!'\n"
                        ),
                    },
                    {
                        "path": "test_feature.py",
                        "expected_sha256": hashes["test_feature.py"],
                        "content": (
                            "import unittest\n\n"
                            "from feature import greet\n\n"
                            "class FeatureTests(unittest.TestCase):\n"
                            "    def test_greet(self):\n"
                            "        self.assertEqual(greet('Ada'), "
                            "'Hello, Ada!')\n"
                        ),
                    },
                ],
            )

            self.assertEqual(result["status"], "applied", result)
            self.assertEqual(
                result["changed_files"],
                ["feature.py", "test_feature.py"],
            )
            self.assertFalse(result["rolled_back"])
            self.assertEqual(
                [check["name"] for check in result["checks"]],
                ["syntax", "fixture_lint", "changed_tests", "verify_behavior"],
            )
            self.assertTrue(all(check["exit_code"] == 0 for check in result["checks"]))
            self.assertIn("return f'Hello, {name}!'", (root / "feature.py").read_text())

    def test_stale_hash_rejects_every_write(self):
        core = load_module("nerd_ufast_core_stale", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            original = (root / "feature.py").read_text()
            result = core.apply_workspace_change(
                root,
                [
                    {
                        "path": "feature.py",
                        "expected_sha256": "0" * 64,
                        "content": "def greet(name):\n    return name\n",
                    }
                ],
            )
            self.assertEqual(result["status"], "stale")
            self.assertEqual((root / "feature.py").read_text(), original)
            self.assertEqual(result["changed_files"], [])

    def test_verification_failure_restores_all_originals(self):
        core = load_module("nerd_ufast_core_rollback_check", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            prepared = core.prepare_workspace_change(root)
            hashes = {item["path"]: item["sha256"] for item in prepared["files"]}
            originals = {
                path: (root / path).read_text()
                for path in ("feature.py", "test_feature.py")
            }
            result = core.apply_workspace_change(
                root,
                [
                    {
                        "path": "feature.py",
                        "expected_sha256": hashes["feature.py"],
                        "content": "def greet(name: str) -> str:\n    return 'wrong'\n",
                    },
                    {
                        "path": "test_feature.py",
                        "expected_sha256": hashes["test_feature.py"],
                        "content": originals["test_feature.py"],
                    },
                ],
            )
            self.assertEqual(result["status"], "verification_failed")
            self.assertTrue(result["rolled_back"])
            self.assertEqual(result["changed_files"], [])
            for path, body in originals.items():
                self.assertEqual((root / path).read_text(), body)

    def test_rejects_traversal_and_symlink_targets(self):
        core = load_module("nerd_ufast_core_paths", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            outside = root.parent / "outside.py"
            outside.write_text("outside = True\n")
            linked = root / "linked.py"
            linked.symlink_to(outside)
            for path in ("../outside.py", "linked.py"):
                with self.subTest(path=path):
                    result = core.apply_workspace_change(
                        root,
                        [
                            {
                                "path": path,
                                "expected_sha256": digest("outside = True\n"),
                                "content": "outside = False\n",
                            }
                        ],
                    )
                    self.assertEqual(result["status"], "rejected")
            self.assertEqual(outside.read_text(), "outside = True\n")

    def test_replace_failure_rolls_back_already_replaced_files(self):
        core = load_module("nerd_ufast_core_rollback_write", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            prepared = core.prepare_workspace_change(root)
            hashes = {item["path"]: item["sha256"] for item in prepared["files"]}
            originals = {
                path: (root / path).read_text()
                for path in ("feature.py", "test_feature.py")
            }
            calls = 0

            def failing_replace(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated replace failure")
                os.replace(source, target)

            result = core.apply_workspace_change(
                root,
                [
                    {
                        "path": "feature.py",
                        "expected_sha256": hashes["feature.py"],
                        "content": "def greet(name):\n    return name\n",
                    },
                    {
                        "path": "test_feature.py",
                        "expected_sha256": hashes["test_feature.py"],
                        "content": originals["test_feature.py"],
                    },
                ],
                replace=failing_replace,
            )
            self.assertEqual(result["status"], "failed")
            self.assertTrue(result["rolled_back"])
            for path, body in originals.items():
                self.assertEqual((root / path).read_text(), body)


class McpProtocolTests(unittest.TestCase):
    def test_stdio_server_initializes_lists_and_calls_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            environment = os.environ.copy()
            environment["NERD_UFAST_WORKSPACE"] = str(root)
            process = subprocess.Popen(
                [sys.executable, str(SERVER_PATH)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )
            assert process.stdin is not None
            assert process.stdout is not None
            requests = (
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {},
                },
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                },
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "ufast_prepare_workspace_change",
                        "arguments": {},
                    },
                },
            )
            responses = []
            for request in requests:
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()
                if "id" in request:
                    responses.append(json.loads(process.stdout.readline()))
            process.stdin.close()
            process.wait(timeout=5)
            process.stdout.close()
            assert process.stderr is not None
            process.stderr.close()

        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(
            [tool["name"] for tool in responses[1]["result"]["tools"]],
            [
                "ufast_prepare_workspace_change",
                "ufast_apply_workspace_change",
            ],
        )
        tool_result = responses[2]["result"]
        self.assertFalse(tool_result["isError"])
        self.assertEqual(tool_result["structuredContent"]["status"], "ready")
        self.assertGreaterEqual(tool_result["structuredContent"]["cold_start_ms"], 0)
        self.assertEqual(
            json.loads(tool_result["content"][0]["text"])["status"],
            "ready",
        )


if __name__ == "__main__":
    unittest.main()
