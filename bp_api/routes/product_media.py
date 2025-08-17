import os
import re

from flask import request
from web import cdn
from web.api import HttpText, json_get, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import File, FileTypeId, Product, ProductMedia, UserRoleLevel
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


@api_bp.post("/products/<int:product_id>/media")
@authorize(UserRoleLevel.ADMIN)
def post_products_id_media(product_id: int) -> Response:
    with conn.begin() as s:
        # Get product
        product = s.query(Product).filter_by(id=product_id).first()
        if not product:
            return json_response(404, HttpText.HTTP_404)

        # Generate sequence number
        sequence = 1
        if config.CDN_AUTO_NAMING:
            last_media = (
                s.query(ProductMedia)
                .filter_by(product_id=product_id)
                .order_by(ProductMedia.id.desc())
                .first()
            )
            if last_media:
                match = re.search(r"(\d+)\.\w+$", last_media.file_.path)
                if match is not None:
                    sequence = int(match.group(1))

        for request_file in request.files.getlist("file"):
            # Increment sequence
            sequence += 1

            # Create details
            if request_file.filename is None:
                continue
            name, extension = os.path.splitext(request_file.filename)
            if config.CDN_AUTO_NAMING:
                name = f"{product.slug}-{sequence}"
            else:
                name = secure_filename(name)
            extension = extension.lstrip(".").lower()
            filename = f"{name}.{extension}"
            path = os.path.join("product", product.slug, filename)

            # Get media type
            if extension in config.CDN_IMAGE_EXTS:
                type_id = FileTypeId.IMAGE
            elif extension in config.CDN_VIDEO_EXTS:
                type_id = FileTypeId.VIDEO
            else:
                continue

            # Upload media
            cdn.upload(request_file, path)

            # Insert file and product media
            file_ = File(path=path, type_id=type_id)
            s.add(file_)
            s.flush()
            product_media = ProductMedia(product_id=product_id, file_id=file_.id)
            s.add(product_media)
            s.flush()

    return json_response()


@api_bp.patch("/products/<int:product_id>/media/<int:media_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_products_id_media_id(product_id: int, media_id: int) -> Response:
    description, has_description = json_get("description", str)
    order, has_order = json_get("order", int)

    with conn.begin() as s:
        # Get product media and file
        product_media = (
            s.query(ProductMedia).filter_by(id=media_id, product_id=product_id).first()
        )
        if not product_media:
            return json_response(404, HttpText.HTTP_404)
        file = s.query(File).filter_by(id=product_media.file_id).first()
        if not file:
            return json_response(404, HttpText.HTTP_404)

        # Update product media and file
        if has_order:
            product_media.order = order
        if has_description:
            file.description = description

    return json_response()


@api_bp.delete("/products/<int:product_id>/media/<int:media_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_products_id_media_id(product_id: int, media_id) -> Response:
    with conn.begin() as s:
        # Get product media and file
        product_media = (
            s.query(ProductMedia).filter_by(id=media_id, product_id=product_id).first()
        )
        if not product_media:
            return json_response(404, HttpText.HTTP_404)
        file = s.query(File).filter_by(id=product_media.file_id).first()
        if not file:
            return json_response(404, HttpText.HTTP_404)

        # Remove file from CDN
        cdn.delete(file.path)

        # Delete product media and file
        s.delete(file)
        s.delete(product_media)

    return json_response()


#
# Functions
#
