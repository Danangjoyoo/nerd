import os
import unittest
from unittest.mock import patch

from config import timeout_seconds


class ConfigTests(unittest.TestCase):
    @patch.dict(os.environ, {"TIMEOUT_SECONDS": "12"})
    def test_timeout_is_an_integer(self):
        self.assertEqual(timeout_seconds(), 12)
        self.assertIsInstance(timeout_seconds(), int)


if __name__ == "__main__":
    unittest.main()
