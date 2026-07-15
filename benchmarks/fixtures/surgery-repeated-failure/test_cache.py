import unittest

from cache import snapshot


class CacheTests(unittest.TestCase):
    def test_each_snapshot_is_isolated(self):
        self.assertEqual(snapshot("first"), ("first",))
        self.assertEqual(snapshot("second"), ("second",))


if __name__ == "__main__":
    unittest.main()
