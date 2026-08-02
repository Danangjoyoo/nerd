import unittest

from normalizers import normalize_handle
from registry import NORMALIZERS


class BehaviorTests(unittest.TestCase):
    def test_handle_rules(self):
        self.assertEqual(normalize_handle("  Jane.Doe+Work  "), "jane_doe_work")
        self.assertEqual(normalize_handle("---Mixed___Separators---"), "mixed_separators")
        self.assertEqual(normalize_handle("AlreadyClean42"), "alreadyclean42")

    def test_handle_is_registered(self):
        self.assertIs(NORMALIZERS["handle"], normalize_handle)
        self.assertEqual(NORMALIZERS["handle"](" A B "), "a_b")


if __name__ == "__main__":
    unittest.main()
