from web.api import HttpText, json_get, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Article, UserRoleLevel
from web.utils.generators import gen_slug
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/articles")
@authorize(UserRoleLevel.ADMIN)
def post_articles() -> Response:
    name, _ = json_get("name", str, nullable=False)

    with conn.begin() as s:
        # Get or restore article
        article = s.query(Article).filter_by(slug=gen_slug(name)).first()
        if article:
            if article.is_deleted:
                article.is_deleted = False
                return json_response()
            else:
                return json_response(409, HttpText.HTTP_409)

        # Insert resource
        article = Article(name=name)
        s.add(article)

    return json_response()


@api_bp.patch("/articles/<int:article_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_articles_id(article_id: int) -> Response:
    attributes, has_attributes = json_get("attributes", dict, default={})
    name, has_name = json_get("name", str)
    summary, has_summary = json_get("summary", str)
    is_visible, has_is_visible = json_get("is_visible", bool)

    with conn.begin() as s:
        # Get article
        article = s.query(Article).filter_by(id=article_id).first()
        if article is None:
            return json_response(404, HttpText.HTTP_404)

        # Update article
        if has_attributes:
            article.attributes = attributes
        if has_name:
            article.name = name
        if has_summary:
            article.summary = summary
        if has_is_visible:
            article.is_visible = is_visible

    return json_response()


@api_bp.delete("/articles/<int:article_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_articles_id(article_id: int) -> Response:
    with conn.begin() as s:
        # Delete article
        article = s.query(Article).filter_by(id=article_id).first()
        if not article:
            return json_response(404, HttpText.HTTP_404)
        article.is_deleted = True

    return json_response()


#
# Functions
#
