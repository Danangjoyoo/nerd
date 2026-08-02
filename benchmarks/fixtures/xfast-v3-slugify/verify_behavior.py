import unittest

from text_tools import slugify


class BehaviorTests(unittest.TestCase):
    def test_normalizes_separator_runs(self):
        self.assertEqual(slugify("  Hello, WORLD!!  "), "hello-world")
        self.assertEqual(slugify("one___two...three"), "one-two-three")

    def test_strips_boundaries_and_handles_empty(self):
        self.assertEqual(slugify("---Already Clean---"), "already-clean")
        self.assertEqual(slugify("!!!"), "")


if __name__ == "__main__":
    unittest.main()
