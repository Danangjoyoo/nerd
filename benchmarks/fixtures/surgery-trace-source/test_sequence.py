import unittest

from sequence import sequence


class SequenceTests(unittest.TestCase):
    def test_size_is_exclusive_upper_bound(self):
        self.assertEqual(sequence(3), [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
