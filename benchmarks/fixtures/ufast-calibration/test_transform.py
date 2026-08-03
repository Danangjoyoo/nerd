import unittest

from transform import triple


class TripleTests(unittest.TestCase):
    def test_positive_value(self):
        self.assertEqual(triple(4), 12)
