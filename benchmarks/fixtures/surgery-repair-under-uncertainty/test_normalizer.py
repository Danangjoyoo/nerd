import unittest

from normalizer import normalize_name


class NormalizerTests(unittest.TestCase):
    def test_trims_and_lowercases(self):
        self.assertEqual(normalize_name("  Ada  "), "ada")


if __name__ == "__main__":
    unittest.main()
