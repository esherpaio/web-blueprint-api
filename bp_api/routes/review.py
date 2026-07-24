import base64
import io
import os
import re
import uuid

from web import cdn
from web.api import HttpText, json_get, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import (
    OrderLine,
    Review,
    ReviewStatusId,
    UserRoleLevel,
    Verification,
    VerificationType,
)
from web.setup import config
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#

MAX_PHOTO_BYTES = 100 * 1024 * 1024
_DATA_URL_RE = re.compile(
    r"data:image/(?P<ext>[\w.+-]+);base64,(?P<data>.+)", re.DOTALL
)


#
# Functions
#


def upload_review_photo(slug: str, data_url: str) -> str | None:
    match = _DATA_URL_RE.match(data_url)
    if match is None:
        return None
    ext = match.group("ext").lower()
    if ext == "jpeg":
        ext = "jpg"
    if ext not in config.CDN_IMAGE_EXTS:
        return None
    try:
        content = base64.b64decode(match.group("data"), validate=True)
    except Exception:
        return None
    if not content or len(content) > MAX_PHOTO_BYTES:
        return None
    path = os.path.join("reviews", f"{slug}-{uuid.uuid4().hex}.{ext}")
    cdn.upload(io.BytesIO(content), path)
    return cdn.url(path)


#
# Endpoints
#


@api_bp.post("/reviews")
def post_reviews() -> Response:
    token, _ = json_get("token", str, nullable=False)
    sku_id, _ = json_get("sku_id", int, nullable=False)
    rating, _ = json_get("rating", int, nullable=False)
    title, _ = json_get("title", str, nullable=False)
    body, _ = json_get("body", str, nullable=False)
    author_name, _ = json_get("author_name", str, nullable=False)
    photo, _ = json_get("photo", str)
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

        # Validate that the SKU belongs to the order
        order_line = (
            s.query(OrderLine).filter_by(order_id=order_id, sku_id=sku_id).first()
        )
        if order_line is None:
            return json_response(404, HttpText.HTTP_404)

        # Prevent duplicate reviews for the same SKU
        existing = s.query(Review).filter_by(order_id=order_id, sku_id=sku_id).first()
        if existing is not None:
            return json_response(409, HttpText.HTTP_409)

        # Upload photo when provided as a base64 data URL
        if photo:
            uploaded = upload_review_photo(order_line.sku.slug, photo)
            if uploaded is not None:
                photo_url = uploaded

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
            status_id=ReviewStatusId.PENDING,
            user_id=verification.user_id,
        )
        s.add(review)

    return json_response()


@api_bp.patch("/reviews/<int:review_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_reviews_id(review_id: int) -> Response:
    status_id, has_status_id = json_get("status_id", str)

    with conn.begin() as s:
        review = s.query(Review).filter_by(id=review_id).first()
        if not review:
            return json_response(404, HttpText.HTTP_404)
        if has_status_id:
            review.status_id = status_id

    return json_response()
