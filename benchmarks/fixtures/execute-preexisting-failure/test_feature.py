import unittest

from numbers import double


class FeatureTests(unittest.TestCase):
    def test_double(self):
        self.assertEqual(double(4), 8)


if __name__ == "__main__":
    unittest.main()
