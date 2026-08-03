import unittest

from transform import triple


class TripleBehaviorTests(unittest.TestCase):
    def test_negative_and_zero_values(self):
        self.assertEqual(triple(-3), -9)
        self.assertEqual(triple(0), 0)
