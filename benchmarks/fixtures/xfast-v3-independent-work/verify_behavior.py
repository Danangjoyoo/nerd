import unittest

from alpha import increment
from beta import decrement


class BehaviorTests(unittest.TestCase):
    def test_increment_across_signs(self):
        self.assertEqual(increment(-2), -1)
        self.assertEqual(increment(0), 1)
        self.assertEqual(increment(8), 9)

    def test_decrement_across_signs(self):
        self.assertEqual(decrement(-2), -3)
        self.assertEqual(decrement(0), -1)
        self.assertEqual(decrement(8), 7)


if __name__ == "__main__":
    unittest.main()
