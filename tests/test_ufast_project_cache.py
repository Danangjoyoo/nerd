import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "docs"
    / "experiments"
    / "nerd-ufast"
    / "skill"
    / "scripts"
    / "project_cache.py"
)


class UFastProjectCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.cache_root = Path(self.temp_dir.name) / "cache"
        self.repo = Path(self.temp_dir.name) / "repo"
        self.repo.mkdir()

    def run_cache(self, *args, check=True):
        env = os.environ.copy()
        env["NERD_UFAST_CACHE_ROOT"] = str(self.cache_root)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=check,
            capture_output=True,
            env=env,
            text=True,
        )

    def test_missing_key_is_a_cache_miss(self):
        result = self.run_cache(
            "get",
            "--repo",
            str(self.repo),
            "--cache",
            "project-map",
            "--key",
            "tests",
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")

    def test_put_uses_exact_markers_and_replaces_a_key(self):
        self.run_cache(
            "put",
            "--repo",
            str(self.repo),
            "--cache",
            "project-map",
            "--key",
            "tests",
            "--value",
            "path: tests/",
        )
        self.run_cache(
            "put",
            "--repo",
            str(self.repo),
            "--cache",
            "project-map",
            "--key",
            "tests",
            "--value",
            "path: test/\ncommand: pytest",
        )

        result = self.run_cache(
            "get",
            "--repo",
            str(self.repo),
            "--cache",
            "project-map",
            "--key",
            "tests",
        )
        cache_file = next(self.cache_root.glob("*/project-map.md"))
        cache_text = cache_file.read_text()

        self.assertEqual(result.stdout, "path: test/\ncommand: pytest\n")
        self.assertEqual(cache_text.count("##@ tests @##"), 1)
        self.assertNotIn("path: tests/", cache_text)

    def test_locked_writers_keep_all_keys(self):
        env = os.environ.copy()
        env["NERD_UFAST_CACHE_ROOT"] = str(self.cache_root)
        base = [
            sys.executable,
            str(SCRIPT),
            "put",
            "--repo",
            str(self.repo),
            "--cache",
            "project-map",
        ]
        writers = [
            subprocess.Popen(
                [*base, "--key", key, "--value", value],
                env=env,
            )
            for key, value in (("api", "src/api"), ("auth", "src/auth"))
        ]

        self.assertEqual([writer.wait() for writer in writers], [0, 0])
        self.assertEqual(
            self.run_cache(
                "get",
                "--repo",
                str(self.repo),
                "--cache",
                "project-map",
                "--key",
                "api",
            ).stdout,
            "src/api\n",
        )
        self.assertEqual(
            self.run_cache(
                "get",
                "--repo",
                str(self.repo),
                "--cache",
                "project-map",
                "--key",
                "auth",
            ).stdout,
            "src/auth\n",
        )

    def test_cache_groups_are_separate(self):
        for cache, key, value in (
            ("conventions", "logging", "Use logger.info()"),
            ("commands", "unit-test", "pytest tests/unit"),
        ):
            self.run_cache(
                "put",
                "--repo",
                str(self.repo),
                "--cache",
                cache,
                "--key",
                key,
                "--value",
                value,
            )

        cache_dir = next(path for path in self.cache_root.iterdir() if path.is_dir())
        self.assertTrue((cache_dir / "conventions.md").is_file())
        self.assertTrue((cache_dir / "commands.md").is_file())
        self.assertEqual(
            self.run_cache(
                "get",
                "--repo",
                str(self.repo),
                "--cache",
                "commands",
                "--key",
                "unit-test",
            ).stdout,
            "pytest tests/unit\n",
        )


if __name__ == "__main__":
    unittest.main()
