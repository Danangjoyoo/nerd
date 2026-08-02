import unittest

from feature import greet


class FeatureTests(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!")


if __name__ == "__main__":
    unittest.main()
