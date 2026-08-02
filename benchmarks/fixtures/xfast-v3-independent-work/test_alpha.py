import unittest

from alpha import increment


class IncrementTests(unittest.TestCase):
    def test_increments_integer(self):
        self.assertEqual(increment(4), 5)


if __name__ == "__main__":
    unittest.main()
