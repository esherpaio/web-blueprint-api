from decimal import Decimal

from web.api import HttpText, json_get, json_response
from web.api.utils.sku import set_sku_unit_prices
from web.auth import authorize
from web.database import conn
from web.database.model import CategoryItem, Product, ProductTypeId, Sku, UserRoleLevel
from web.utils.generators import gen_slug
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/products")
@authorize(UserRoleLevel.ADMIN)
def post_products() -> Response:
    name, _ = json_get("name", str, nullable=False)
    unit_price, _ = json_get("unit_price", Decimal, nullable=True, default=1)

    with conn.begin() as s:
        # Get or restore product
        product = s.query(Product).filter_by(slug=gen_slug(name)).first()
        if product:
            if product.is_deleted:
                return json_response()
            else:
                return json_response(409, HttpText.HTTP_409)

        # Insert product
        product = Product(
            type_id=ProductTypeId.PHYSICAL,
            name=name,
            unit_price=unit_price,
        )
        s.add(product)

    return json_response()


@api_bp.patch("/products/<int:product_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_products_id(product_id: int) -> Response:
    attributes, has_attributes = json_get("attributes", dict, default={})
    file_url, has_file_url = json_get("file_url", str)
    consent_required, has_consent_required = json_get("consent_required", bool)
    shipment_class_id, has_shipment_class_id = json_get("shipment_class_id", int)
    summary, has_summary = json_get("summary", str)
    type_id, has_type_id = json_get("type_id", int)
    unit_price, has_unit_price = json_get("unit_price", Decimal)

    with conn.begin() as s:
        # Get product
        product = s.query(Product).filter_by(id=product_id).first()
        if product is None:
            return json_response(404, HttpText.HTTP_404)

        # Update product
        if has_attributes:
            product.attributes = attributes
        if has_type_id:
            product.type_id = type_id
        if has_shipment_class_id:
            product.shipment_class_id = shipment_class_id
        if has_summary:
            product.summary = summary
        if has_unit_price:
            product.unit_price = unit_price
            set_sku_unit_prices(s, product_ids=[product.id])
        if has_consent_required:
            product.consent_required = consent_required
        if has_file_url:
            product.file_url = file_url

    return json_response()


@api_bp.delete("/products/<int:product_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_products_id(product_id: int) -> Response:
    with conn.begin() as s:
        # Delete product
        product = s.query(Product).filter_by(id=product_id).first()
        if not product:
            return json_response(404, HttpText.HTTP_404)
        product.is_deleted = True

        # Delete skus
        skus = s.query(Sku).filter(Sku.product_id == product_id).all()
        for sku in skus:
            sku.is_deleted = True

            # Delete category items
            category_items = s.query(CategoryItem).filter_by(sku_id=sku.id).all()
            for category_item in category_items:
                s.delete(category_item)

    return json_response()


#
# Functions
#
