"""Order intake with the same coupon rule copy-pasted at three call sites."""


def create_order(payload):
    coupon = payload.get("coupon", "")
    if coupon and (len(coupon) < 4 or not coupon.isalnum()):
        raise ValueError("invalid coupon")
    return {"id": payload["id"], "coupon": coupon, "state": "created"}


def update_order(order, payload):
    coupon = payload.get("coupon", "")
    if coupon and (len(coupon) < 4 or not coupon.isalnum()):
        raise ValueError("invalid coupon")
    order["coupon"] = coupon
    return order


def import_order(row):
    coupon = row[2]
    if coupon and (len(coupon) < 4 or not coupon.isalnum()):
        raise ValueError("invalid coupon")
    return {"id": row[0], "coupon": coupon, "state": "imported"}
