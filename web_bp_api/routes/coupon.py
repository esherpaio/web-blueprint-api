from decimal import Decimal

from web.api import HttpText, json_get, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Coupon, UserRoleLevel
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/coupons")
@authorize(UserRoleLevel.ADMIN)
def post_coupons() -> Response:
    amount, _ = json_get("amount", Decimal)
    code, _ = json_get("code", str, nullable=False)
    percentage, _ = json_get("percentage", int)
    rate = abs(percentage / 100 - 1) if percentage else None

    with conn.begin() as s:
        # Check if coupon already exists
        coupon = s.query(Coupon).filter_by(code=code, is_deleted=False).first()
        if coupon:
            return json_response(409, HttpText.HTTP_409)

        # Insert coupon
        coupon = Coupon(code=code, rate=rate, amount=amount)
        s.add(coupon)

    return json_response()


@api_bp.delete("/coupons/<int:coupon_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_coupons_id(coupon_id: int) -> Response:
    with conn.begin() as s:
        # Delete coupon
        coupon = s.query(Coupon).filter_by(id=coupon_id).first()
        if not coupon:
            return json_response(404, HttpText.HTTP_404)
        coupon.is_deleted = True

    return json_response()


#
# Functions
#
