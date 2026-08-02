import unittest

from beta import decrement


class DecrementTests(unittest.TestCase):
    def test_decrements_integer(self):
        self.assertEqual(decrement(4), 3)


if __name__ == "__main__":
    unittest.main()
