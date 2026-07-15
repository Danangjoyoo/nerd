import unittest


class LegacyTests(unittest.TestCase):
    def test_preexisting_failure(self):
        self.assertEqual("legacy", "still-broken")


if __name__ == "__main__":
    unittest.main()
