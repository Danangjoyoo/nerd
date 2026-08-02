import unittest

from alpha import clamp
from beta import parity_label


class BehaviorTests(unittest.TestCase):
    def test_clamp_inside_and_at_bounds(self):
        self.assertEqual(clamp(5, 1, 10), 5)
        self.assertEqual(clamp(1, 1, 10), 1)
        self.assertEqual(clamp(10, 1, 10), 10)

    def test_clamp_outside_bounds(self):
        self.assertEqual(clamp(-3, 1, 10), 1)
        self.assertEqual(clamp(14, 1, 10), 10)

    def test_parity_label_handles_signs_and_zero(self):
        self.assertEqual(parity_label(0), "even")
        self.assertEqual(parity_label(-3), "odd")
        self.assertEqual(parity_label(8), "even")


if __name__ == "__main__":
    unittest.main()
