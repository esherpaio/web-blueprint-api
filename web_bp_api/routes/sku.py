from web.api import API, HttpText, json_get, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import (
    CategoryItem,
    ProductLink,
    Sku,
    UserRoleLevel,
)
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


class SkuAPI(API):
    model = Sku
    get_columns = {
        Sku.id,
        Sku.slug,
        Sku.stock,
        Sku.unit_price,
        Sku.is_deleted,
        Sku.is_visible,
        Sku.product_id,
        "name",
    }
    get_filters = {
        Sku.is_deleted,
    }


#
# Endpoints
#


@api_bp.patch("/skus/<int:sku_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_skus_id(sku_id: int) -> Response:
    attributes, has_attributes = json_get("attributes", dict, default={})
    is_visible, has_is_visible = json_get("is_visible", bool)
    number, has_number = json_get("number", str)
    stock, has_stock = json_get("stock", int)

    with conn.begin() as s:
        # Get sku
        sku = s.query(Sku).filter_by(id=sku_id).first()
        if not sku:
            return json_response(404, HttpText.HTTP_404)

        # Update sku
        if has_attributes:
            sku.attributes = attributes
        if has_is_visible:
            sku.is_visible = is_visible
        if has_stock:
            sku.stock = stock
        if has_number:
            sku.number = number

    return json_response()


@api_bp.get("/skus")
@authorize(UserRoleLevel.ADMIN)
def get_skus() -> Response:
    api = SkuAPI()
    data = api.gen_query_data(api.get_filters)
    with conn.begin() as s:
        filters = api.gen_query_filters(data)
        models: list[Sku] = api.list_(s, *filters, order_by=Sku.slug)
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


@api_bp.delete("/skus/<int:sku_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_skus_id(sku_id: int) -> Response:
    with conn.begin() as s:
        # Delete sku
        sku = s.query(Sku).filter_by(id=sku_id).first()
        if not sku:
            return json_response(404, HttpText.HTTP_404)
        sku.number = None
        sku.is_deleted = True

        # Delete category items
        category_items = s.query(CategoryItem).filter_by(sku_id=sku_id).all()
        for category_item in category_items:
            s.delete(category_item)

        # Delete product links
        product_links = s.query(ProductLink).filter_by(sku_id=sku_id).all()
        for product_link in product_links:
            s.delete(product_link)

    return json_response()


#
# Functions
#
