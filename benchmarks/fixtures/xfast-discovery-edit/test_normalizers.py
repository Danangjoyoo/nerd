import unittest

from normalizers import normalize_label, normalize_slug


class NormalizerTests(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(normalize_slug("  Hello, World!  "), "hello-world")

    def test_label(self):
        self.assertEqual(normalize_label("  Hello   World  "), "Hello World")


if __name__ == "__main__":
    unittest.main()
