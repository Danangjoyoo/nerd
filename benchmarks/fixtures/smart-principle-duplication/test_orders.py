import unittest

from orders import create_order, import_order, update_order


class CouponValidationTests(unittest.TestCase):
    def test_create_rejects_short_coupon(self):
        with self.assertRaises(ValueError):
            create_order({"id": 1, "coupon": "ab"})

    def test_update_rejects_short_coupon(self):
        with self.assertRaises(ValueError):
            update_order({"id": 1, "coupon": ""}, {"coupon": "ab"})

    def test_import_rejects_short_coupon(self):
        with self.assertRaises(ValueError):
            import_order([1, "n", "ab"])

    def test_valid_coupon_is_accepted_everywhere(self):
        self.assertEqual(create_order({"id": 1, "coupon": "SAVE10"})["coupon"], "SAVE10")
        self.assertEqual(
            update_order({"id": 1, "coupon": ""}, {"coupon": "SAVE10"})["coupon"],
            "SAVE10",
        )
        self.assertEqual(import_order([1, "n", "SAVE10"])["coupon"], "SAVE10")


if __name__ == "__main__":
    unittest.main()
