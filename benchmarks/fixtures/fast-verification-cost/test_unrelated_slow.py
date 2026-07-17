import time
import unittest


class UnrelatedSlowTests(unittest.TestCase):
    def test_unrelated_slow_boundary(self):
        time.sleep(2)
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
