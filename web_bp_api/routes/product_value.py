from decimal import Decimal

from sqlalchemy import false
from sqlalchemy.orm import contains_eager
from web.api import HttpText, json_get, json_response
from web.api.utils.sku import set_sku_unit_prices
from web.auth import authorize
from web.database import conn
from web.database.model import ProductValue, Sku, SkuDetail, UserRoleLevel
from web.utils.generators import gen_slug
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/products/<int:product_id>/values")
@authorize(UserRoleLevel.ADMIN)
def post_products_id_values(product_id: int) -> Response:
    name, _ = json_get("name", str, nullable=False)
    option_id, _ = json_get("option_id", int, nullable=False)
    order, _ = json_get("order", int)
    unit_price, _ = json_get("unit_price", Decimal, nullable=True)

    with conn.begin() as s:
        # Get or restore product value
        product_value = (
            s.query(ProductValue)
            .filter_by(option_id=option_id, slug=gen_slug(name))
            .first()
        )
        if product_value:
            if product_value.is_deleted:
                product_value.is_deleted = False
                return json_response()
            else:
                return json_response(409, HttpText.HTTP_409)

        # Insert product value
        product_value = ProductValue(
            option_id=option_id,
            name=name,
            unit_price=unit_price,
            order=order,
        )
        s.add(product_value)

    return json_response()


@api_bp.patch("/products/<int:product_id>/values/<int:value_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_products_id_values_id(product_id: int, value_id: int) -> Response:
    media_id, has_media_id = json_get("media_id", int)
    order, has_order = json_get("order", int)
    unit_price, has_unit_price = json_get("unit_price", Decimal)

    with conn.begin() as s:
        # Get product value
        product_value = s.query(ProductValue).filter_by(id=value_id).first()
        if not product_value:
            return json_response(404, HttpText.HTTP_404)

        # Update product value
        if has_media_id:
            product_value.media_id = media_id
        if has_unit_price:
            product_value.unit_price = unit_price
            set_sku_unit_prices(s, value_ids=[product_value.id])
        if has_order:
            product_value.order = order

    return json_response()


@api_bp.delete("/products/<int:product_id>/values/<int:value_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_products_id_values_id(product_id: int, value_id: int) -> Response:
    with conn.begin() as s:
        # Delete product value
        product_value = s.query(ProductValue).filter_by(id=value_id).first()
        if not product_value:
            return json_response(404, HttpText.HTTP_404)
        product_value.is_deleted = True

        # Delete skus
        skus = (
            s.query(Sku)
            .join(Sku.details)
            .options(contains_eager(Sku.details))
            .filter(SkuDetail.value_id == value_id, Sku.is_deleted == false())
            .all()
        )
        for sku in skus:
            sku.is_deleted = True

    return json_response()


#
# Functions
#
