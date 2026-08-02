import unittest

from feature import greet


class BehaviorTests(unittest.TestCase):
    def test_preserves_supplied_name(self):
        self.assertEqual(greet("Grace Hopper"), "Hello, Grace Hopper!")
        self.assertEqual(greet("Lin 李"), "Hello, Lin 李!")

    def test_empty_name(self):
        self.assertEqual(greet(""), "Hello, !")


if __name__ == "__main__":
    unittest.main()
