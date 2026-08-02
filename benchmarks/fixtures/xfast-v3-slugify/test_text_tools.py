import unittest

from text_tools import clean_text, slugify


class TextToolsTests(unittest.TestCase):
    def test_clean_text(self):
        self.assertEqual(clean_text("  Ada Lovelace "), "ada lovelace")

    def test_slugify(self):
        self.assertEqual(slugify("  Ada Lovelace  "), "ada-lovelace")


if __name__ == "__main__":
    unittest.main()
