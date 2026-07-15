import unittest

from formatter import normalize_spaces


class FormatterTests(unittest.TestCase):
    def test_collapses_repeated_spaces(self):
        self.assertEqual(normalize_spaces("a   b"), "a b")


if __name__ == "__main__":
    unittest.main()
