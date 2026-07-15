import unittest

from stats import average


class StatsTests(unittest.TestCase):
    def test_average(self):
        self.assertEqual(average([1, 2, 6]), 3)

    def test_empty_values_are_rejected(self):
        with self.assertRaises(ValueError):
            average([])


if __name__ == "__main__":
    unittest.main()
