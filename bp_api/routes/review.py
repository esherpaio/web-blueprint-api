import os

from flask import request
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
from werkzeug.utils import secure_filename

from bp_api import api_bp

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/reviews")
def post_reviews() -> Response:
    token = request.form.get("token")
    sku_id_raw = request.form.get("sku_id")
    rating_raw = request.form.get("rating")
    title = request.form.get("title")
    body = request.form.get("body")
    author_name = request.form.get("author_name")
    photo_url = request.form.get("photo_url")
    show_photo = request.form.get("show_photo", "true").lower() == "true"

    if not all([token, sku_id_raw, rating_raw, title, body, author_name]):
        return json_response(400, HttpText.HTTP_400)
    try:
        sku_id = int(sku_id_raw)  # type: ignore[arg-type]
        rating = int(rating_raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return json_response(400, HttpText.HTTP_400)

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

        # Upload photo when provided
        request_file = request.files.get("photo")
        if request_file is not None and request_file.filename:
            _, extension = os.path.splitext(request_file.filename)
            extension = extension.lstrip(".").lower()
            if extension in config.CDN_IMAGE_EXTS:
                filename = secure_filename(f"{token}-{sku_id}.{extension}")
                path = os.path.join("review", str(token), filename)
                cdn.upload(request_file, path)
                photo_url = cdn.url(path)

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
