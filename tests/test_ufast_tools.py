from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = (
    ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_core.py"
)
SERVER_PATH = (
    ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_mcp.py"
)
INDEX_PATH = (
    ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_index.py"
)
VERIFY_PATH = (
    ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_verify.py"
)
REGISTRY_PATH = (
    ROOT / "skills" / "nerd-ufast" / "scripts" / "ufast_registry.py"
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
            self.assertEqual(
                [check["name"] for check in result["checks"]],
                ["structural_validation"],
            )
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
                [
                    "structural_validation",
                    "python_syntax",
                    "fixture_lint",
                    "python_tests",
                    "verify_behavior",
                ],
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


class ProjectIndexContractTests(unittest.TestCase):
    def test_builds_reuses_and_invalidates_a_content_cache(self):
        index_module = load_module("nerd_ufast_index_cache", INDEX_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            project = index_module.ProjectIndex(root)

            first = project.project_index()
            second = project.project_index()
            (root / "feature.py").write_text(
                "def greet(name: str) -> str:\n    return name\n",
                encoding="utf-8",
            )
            third = project.project_index()

        self.assertEqual(first["status"], "ready")
        self.assertEqual(first["cache_status"], "rebuilt")
        self.assertEqual(second["cache_status"], "hit")
        self.assertEqual(third["cache_status"], "rebuilt")
        self.assertEqual(first["total_files"], 2)
        self.assertEqual(
            [item["path"] for item in first["files"]],
            ["feature.py", "test_feature.py"],
        )
        self.assertNotIn("content", first["files"][0])
        self.assertNotEqual(first["index_id"], third["index_id"])

    def test_fast_search_returns_bounded_context_and_edit_hashes(self):
        index_module = load_module("nerd_ufast_index_search", INDEX_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            project = index_module.ProjectIndex(root)
            matched = project.fast_search(
                "NotImplementedError",
                mode="literal",
                max_results=3,
                context_lines=1,
            )
            invalid = project.fast_search("[", mode="regex")
            batched = project.fast_search(
                queries=["NotImplementedError", "FeatureTests"],
                max_results=4,
            )
            ambiguous = project.fast_search(
                "NotImplementedError",
                queries=["FeatureTests"],
            )

        self.assertEqual(matched["status"], "matched")
        self.assertEqual(matched["match_count"], 1)
        self.assertEqual(matched["matches"][0]["path"], "feature.py")
        self.assertEqual(
            matched["matches"][0]["sha256"],
            digest("def greet(name: str) -> str:\n    raise NotImplementedError\n"),
        )
        self.assertIn("NotImplementedError", matched["matches"][0]["preview"])
        self.assertEqual(invalid["status"], "rejected")
        self.assertIn("regular expression", invalid["reason"])
        self.assertEqual(batched["status"], "matched")
        self.assertEqual(batched["queries"], ["NotImplementedError", "FeatureTests"])
        self.assertEqual(batched["query_counts"], {"NotImplementedError": 1, "FeatureTests": 1})
        self.assertEqual({match["query"] for match in batched["matches"]}, set(batched["queries"]))
        self.assertEqual(ambiguous["status"], "rejected")
        self.assertIn("Exactly one", ambiguous["reason"])


class PhaseOneSafeEditTests(unittest.TestCase):
    def test_exact_replacements_are_applied_by_the_tool(self):
        core = load_module("nerd_ufast_core_replacements", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            original = (root / "feature.py").read_text(encoding="utf-8")
            result = core.safe_edit(
                root,
                [
                    {
                        "path": "feature.py",
                        "expected_sha256": digest(original),
                        "replacements": [
                            {
                                "old_text": "    raise NotImplementedError\n",
                                "new_text": "    return f'Hello, {name}!'\n",
                                "expected_occurrences": 1,
                            }
                        ],
                    }
                ],
                verify=False,
            )

        self.assertEqual(result["status"], "applied", result)
        self.assertEqual(result["edit_mode"], "exact_replacements")
        self.assertEqual(result["resulting_files"][0]["path"], "feature.py")
        self.assertEqual(
            result["resulting_files"][0]["sha256"],
            digest("def greet(name: str) -> str:\n    return f'Hello, {name}!'\n"),
        )
        self.assertNotIn("content", result["resulting_files"][0])

    def test_ambiguous_replacement_rejects_the_complete_batch(self):
        core = load_module("nerd_ufast_core_replacement_reject", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "notes.txt"
            original = "same\nsame\n"
            path.write_text(original, encoding="utf-8")
            result = core.safe_edit(
                root,
                [
                    {
                        "path": "notes.txt",
                        "expected_sha256": digest(original),
                        "replacements": [
                            {
                                "old_text": "same",
                                "new_text": "changed",
                                "expected_occurrences": 1,
                            }
                        ],
                    }
                ],
                verify=False,
            )
            preserved = path.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "rejected")
        self.assertIn("occurrence", result["reason"])
        self.assertEqual(preserved, original)


class TestRunnerContractTests(unittest.TestCase):
    def test_detects_and_runs_repository_owned_python_checks(self):
        verify = load_module("nerd_ufast_verify_python", VERIFY_PATH)
        core = load_module("nerd_ufast_core_verify_python", CORE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            plan = verify.detect_test_plan(root, ["feature.py", "test_feature.py"])
            original = (root / "feature.py").read_text(encoding="utf-8")
            edited = core.safe_edit(
                root,
                [
                    {
                        "path": "feature.py",
                        "expected_sha256": digest(original),
                        "replacements": [
                            {
                                "old_text": "    raise NotImplementedError\n",
                                "new_text": "    return f'Hello, {name}!'\n",
                                "expected_occurrences": 1,
                            }
                        ],
                    }
                ],
                verify=False,
            )
            self.assertEqual(edited["status"], "applied")
            result = verify.run_test_plan(root, ["feature.py", "test_feature.py"])

        self.assertEqual(
            [check.name for check in plan],
            ["python_syntax", "fixture_lint", "python_tests", "verify_behavior"],
        )
        self.assertEqual(result["status"], "passed", result)
        self.assertTrue(all(check["exit_code"] == 0 for check in result["checks"]))

    def test_detects_common_language_backends_without_installing_them(self):
        verify = load_module("nerd_ufast_verify_backends", VERIFY_PATH)
        cases = {
            "package.json": "node_test",
            "go.mod": "go_test",
            "Cargo.toml": "cargo_test",
            "pom.xml": "maven_test",
            "gradlew": "gradle_test",
        }
        for marker, expected in cases.items():
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                body = '{"scripts":{"test":"node --test"}}\n' if marker == "package.json" else "fixture\n"
                path = root / marker
                path.write_text(body, encoding="utf-8")
                if marker == "gradlew":
                    path.chmod(0o755)
                plan = verify.detect_test_plan(root, [])
                self.assertIn(expected, [check.name for check in plan])

    def test_limits_detection_to_the_changed_language_and_skips_dependencies(self):
        verify = load_module("nerd_ufast_verify_relevance", VERIFY_PATH)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.md").write_text("before\n", encoding="utf-8")
            (root / "package.json").write_text(
                '{"scripts":{"test":"node --test"}}\n',
                encoding="utf-8",
            )
            dependencies = root / "node_modules" / "nested"
            dependencies.mkdir(parents=True)
            (dependencies / "test_hidden.py").write_text(
                "raise RuntimeError('must not run')\n",
                encoding="utf-8",
            )

            plan = verify.detect_test_plan(root, ["notes.md"])

        self.assertEqual(plan, [])

    def test_runs_independent_checks_concurrently_in_registry_order(self):
        verify = load_module("nerd_ufast_verify_concurrent", VERIFY_PATH)
        plan = [
            verify.CheckSpec("slow", "fixture", (sys.executable, "-V")),
            verify.CheckSpec("fast", "fixture", (sys.executable, "-V")),
        ]
        verify.detect_test_plan = lambda *_args, **_kwargs: plan

        def fake_run(_workspace, check):
            time.sleep(0.12)
            return {
                "name": check.name,
                "backend": check.backend,
                "exit_code": 0,
                "duration_ms": 1,
                "output": "",
            }

        verify._run_check = fake_run
        with tempfile.TemporaryDirectory() as directory:
            started = time.perf_counter()
            result = verify.run_test_plan(directory)
            elapsed = time.perf_counter() - started

        self.assertEqual(result["status"], "passed")
        self.assertEqual([check["name"] for check in result["checks"]], ["slow", "fast"])
        self.assertLess(elapsed, 0.20)


class OperationRegistryContractTests(unittest.TestCase):
    def test_routes_phase_one_intents_and_reserves_semantic_extensions(self):
        registry_module = load_module("nerd_ufast_registry_contract", REGISTRY_PATH)
        registry = registry_module.phase_one_registry(
            project_index=lambda _: {"status": "ready"},
            fast_search=lambda _: {"status": "matched"},
            safe_edit=lambda _: {"status": "applied"},
            test_runner=lambda _: {"status": "passed"},
        )

        self.assertEqual(
            [tool["name"] for tool in registry.tool_definitions()],
            [
                "ufast_project_index",
                "ufast_fast_search",
                "ufast_safe_edit",
                "ufast_test_runner",
            ],
        )
        definitions = {tool["name"]: tool for tool in registry.tool_definitions()}
        self.assertIn("queries", definitions["ufast_fast_search"]["inputSchema"]["properties"])
        edit_definition = definitions["ufast_safe_edit"]
        edit_properties = edit_definition["inputSchema"]["properties"]["changes"]["items"]["properties"]
        self.assertIn("sha256", edit_properties)
        self.assertIn("old_text", edit_properties)
        self.assertFalse(edit_definition["annotations"]["readOnlyHint"])
        self.assertFalse(edit_definition["annotations"]["destructiveHint"])
        self.assertEqual(
            registry.route_for_intent("search_project").name,
            "ufast_fast_search",
        )
        self.assertIsNone(registry.route_for_intent("rename_symbol"))
        routed = registry.dispatch("ufast_safe_edit", {"changes": []})
        self.assertEqual(routed["route"], "safe_edit")
        self.assertEqual(routed["backend"], "workspace_transaction")

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
                        "name": "ufast_project_index",
                        "arguments": {},
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "ufast_fast_search",
                        "arguments": {
                            "queries": ["NotImplementedError", "FeatureTests"]
                        },
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "ufast_safe_edit",
                        "arguments": {
                            "changes": [
                                {
                                    "path": "feature.py",
                                    "sha256": digest(
                                        "def greet(name: str) -> str:\n"
                                        "    raise NotImplementedError\n"
                                    ),
                                    "old_text": "def greet(name: str) -> str:\n",
                                    "new_text": (
                                        "def greet(name: str) -> str:\n"
                                        "    \"\"\"Return a personalized greeting.\"\"\"\n"
                                    ),
                                },
                                {
                                    "path": "feature.py",
                                    "sha256": digest(
                                        "def greet(name: str) -> str:\n"
                                        "    raise NotImplementedError\n"
                                    ),
                                    "old_text": "    raise NotImplementedError\n",
                                    "new_text": "    return f'Hello, {name}!'\n",
                                }
                            ]
                        },
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {
                        "name": "ufast_test_runner",
                        "arguments": {"changed_paths": ["feature.py"]},
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
                "ufast_project_index",
                "ufast_fast_search",
                "ufast_safe_edit",
                "ufast_test_runner",
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
        self.assertEqual(responses[3]["result"]["structuredContent"]["status"], "matched")
        self.assertEqual(
            responses[3]["result"]["structuredContent"]["queries"],
            ["NotImplementedError", "FeatureTests"],
        )
        self.assertEqual(
            responses[3]["result"]["structuredContent"]["route"],
            "search_project",
        )
        self.assertEqual(responses[4]["result"]["structuredContent"]["status"], "applied")
        self.assertEqual(responses[4]["result"]["structuredContent"]["route"], "safe_edit")
        self.assertEqual(
            responses[4]["result"]["structuredContent"]["edit_mode"],
            "exact_replacements",
        )
        self.assertEqual(responses[5]["result"]["structuredContent"]["status"], "passed")
        self.assertEqual(
            responses[5]["result"]["structuredContent"]["route"],
            "test_runner",
        )


if __name__ == "__main__":
    unittest.main()
