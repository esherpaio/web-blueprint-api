import os
import re

from flask import request
from web import cdn
from web.api import HttpText, json_get, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Article, ArticleMedia, File, FileTypeId, UserRoleLevel
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


@api_bp.post("/articles/<int:article_id>/media")
@authorize(UserRoleLevel.ADMIN)
def post_articles_id_media(article_id: int) -> Response:
    with conn.begin() as s:
        # Get article
        article = s.query(Article).filter_by(id=article_id).first()
        if not article:
            return json_response(404, HttpText.HTTP_404)

        # Generate sequence number
        sequence = 1
        if config.CDN_AUTO_NAMING:
            last_media = (
                s.query(ArticleMedia)
                .filter_by(article_id=article_id)
                .order_by(ArticleMedia.id.desc())
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
                name = f"{article.slug}-{sequence}"
            else:
                name = secure_filename(name)
            extension = extension.lstrip(".").lower()
            filename = f"{name}.{extension}"
            path = os.path.join("article", article.slug, filename)

            # Get media type
            if extension in config.CDN_IMAGE_EXTS:
                type_id = FileTypeId.IMAGE
            elif extension in config.CDN_VIDEO_EXTS:
                type_id = FileTypeId.VIDEO
            else:
                continue

            # Upload media
            cdn.upload(request_file, path)

            # Insert file and article media
            file_ = File(path=path, type_id=type_id)
            s.add(file_)
            s.flush()
            article_media = ArticleMedia(article_id=article_id, file_id=file_.id)
            s.add(article_media)

    return json_response()


@api_bp.patch("/articles/<int:article_id>/media/<int:media_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_articles_id_media_id(article_id: int, media_id: int) -> Response:
    description, has_description = json_get("description", str)
    order, has_order = json_get("order", int)

    with conn.begin() as s:
        # Get article media and file
        article_media = (
            s.query(ArticleMedia).filter_by(id=media_id, article_id=article_id).first()
        )
        if not article_media:
            return json_response(404, HttpText.HTTP_404)
        file_ = s.query(File).filter_by(id=article_media.file_id).first()
        if not file_:
            return json_response(404, HttpText.HTTP_404)

        # Update article media and file
        if has_order:
            article_media.order = order
        if has_description:
            file_.description = description

    return json_response()


@api_bp.delete("/articles/<int:article_id>/media/<int:media_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_articles_id_media_id(article_id: int, media_id: int) -> Response:
    with conn.begin() as s:
        # Get article media and file
        article_media = (
            s.query(ArticleMedia).filter_by(id=media_id, article_id=article_id).first()
        )
        if not article_media:
            return json_response(404, HttpText.HTTP_404)
        file_ = s.query(File).filter_by(id=article_media.file_id).first()
        if not file_:
            return json_response(404, HttpText.HTTP_404)

        # Delete file from CDN
        cdn.delete(file_.path)

        # Delete article media and file
        s.delete(file_)
        s.delete(article_media)

    return json_response()


#
# Functions
#
