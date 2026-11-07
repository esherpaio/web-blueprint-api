from web.api import HttpText, json_get, json_response
from web.database import conn
from web.database.model import (
    OrderLine,
    Review,
    ReviewStatusId,
    Verification,
    VerificationType,
)
from werkzeug import Response

from bp_api import api_bp

#
# Endpoints
#


@api_bp.post("/reviews")
def post_reviews() -> Response:
    token, _ = json_get("token", str, nullable=False)
    sku_id, _ = json_get("sku_id", int, nullable=False)
    rating, _ = json_get("rating", int, nullable=False)
    title, _ = json_get("title", str)
    body, _ = json_get("body", str)
    author_name, _ = json_get("author_name", str)
    photo_url, _ = json_get("photo_url", str)
    show_photo, _ = json_get("show_photo", bool, default=False)

    with conn.begin() as s:
        # Validate review token
        verification = (
            s.query(Verification)
            .filter_by(key=token, type=VerificationType.REVIEW)
            .first()
        )
        if verification is None:
            return json_response(404, HttpText.HTTP_404)
        if not verification.is_valid:
            return json_response(410, HttpText.HTTP_410)
        order_id = verification.data.get("order_id")

        # Validate SKU to order
        order_line = (
            s.query(OrderLine).filter_by(order_id=order_id, sku_id=sku_id).first()
        )
        if order_line is None:
            return json_response(404, HttpText.HTTP_404)

        # Prevent duplicate reviews
        existing = s.query(Review).filter_by(order_id=order_id, sku_id=sku_id).first()
        if existing is not None:
            return json_response(409, HttpText.HTTP_409)

        # Determine review status
        if not title and not body and not author_name:
            status_id = ReviewStatusId.APPROVED
        else:
            status_id = ReviewStatusId.PENDING

        # Insert review
        review = Review(
            author_name=author_name,
            body=body,
            title=title,
            rating=rating,
            photo_url=photo_url,
            show_photo=show_photo,
            order_id=order_id,
            product_id=order_line.sku.product_id,
            sku_id=sku_id,
            status_id=status_id,
            user_id=verification.user_id,
        )
        s.add(review)
        s.flush()

    return json_response()
