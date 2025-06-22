from web.api import HttpText, json_get, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import CategoryItem, UserRoleLevel
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/categories/<int:category_id>/items")
@authorize(UserRoleLevel.ADMIN)
def post_categories_id_items(category_id: int) -> Response:
    order, _ = json_get("order", int)
    sku_id, _ = json_get("sku_id", int)
    article_id, _ = json_get("article_id", int)

    with conn.begin() as s:
        # Check if category item already exists
        category_item = (
            s.query(CategoryItem)
            .filter_by(article_id=article_id, category_id=category_id, sku_id=sku_id)
            .first()
        )
        if category_item:
            return json_response(409, HttpText.HTTP_409)

        # Insert category item
        category_item = CategoryItem(
            article_id=article_id,
            category_id=category_id,
            sku_id=sku_id,
            order=order,
        )
        s.add(category_item)

    return json_response()


@api_bp.patch("/categories/<int:category_id>/items/<int:item_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_categories_id_items_id(category_id: int, item_id: int) -> Response:
    order, has_order = json_get("order", int)

    with conn.begin() as s:
        # Get category item
        category_item = (
            s.query(CategoryItem).filter_by(id=item_id, category_id=category_id).first()
        )
        if not category_item:
            return json_response(404, HttpText.HTTP_404)

        # Update category item
        if has_order:
            category_item.order = order

    return json_response()


@api_bp.delete("/categories/<int:category_id>/items/<int:item_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_categories_id_items_id(category_id: int, item_id: int) -> Response:
    with conn.begin() as s:
        # Delete category item
        category_item = (
            s.query(CategoryItem).filter_by(id=item_id, category_id=category_id).first()
        )
        if not category_item:
            return json_response(404, HttpText.HTTP_404)
        s.delete(category_item)

    return json_response()


#
# Functions
#
