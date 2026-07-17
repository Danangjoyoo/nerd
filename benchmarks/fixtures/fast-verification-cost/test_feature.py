import unittest

from feature import normalize


class NormalizeTests(unittest.TestCase):
    def test_strips_and_lowercases_text(self):
        self.assertEqual(normalize("  Hello WORLD  "), "hello world")


if __name__ == "__main__":
    unittest.main()
