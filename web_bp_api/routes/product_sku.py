import itertools

from web.api import HttpText, json_response
from web.api.utils.sku import get_sku_unit_price
from web.auth import authorize
from web.database import conn
from web.database.model import Product, ProductValue, Sku, SkuDetail, UserRoleLevel
from web.logger import log
from web.utils.generators import gen_slug
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/products/<int:product_id>/skus")
@authorize(UserRoleLevel.ADMIN)
def post_skus(product_id: int) -> Response:
    with conn.begin() as s:
        # Get product and skus
        skus = s.query(Sku).filter_by(product_id=product_id).all()
        product = s.query(Product).filter_by(id=product_id).first()
        if product is None:
            return json_response(404, HttpText.HTTP_404)

        # Generate all possible combinations between value_ids
        value_id_sets = []
        options = [x for x in product.options if not x.is_deleted]
        for option in options:
            option_value_ids = [x.id for x in option.values if not x.is_deleted]
            value_id_sets.append(option_value_ids)
        value_id_groups = list(itertools.product(*value_id_sets))

        for value_ids in value_id_groups:
            values = (
                s.query(ProductValue)
                .filter(ProductValue.id.in_(value_ids))
                .order_by(ProductValue.id)
                .all()
            )
            sku = next((x for x in skus if x.value_ids == sorted(value_ids)), None)
            if sku is not None:
                log.info("Restoring SKU %d", sku.id)
                sku.is_deleted = False
            else:
                slug_parts = [product.name, *(x.name for x in values)]
                slug = gen_slug("-".join(slug_parts))
                unit_price = get_sku_unit_price(product, values)
                sku = Sku(
                    product_id=product_id,
                    slug=slug,
                    stock=1,
                    is_visible=True,
                    unit_price=unit_price,
                )
                s.add(sku)
                s.flush()
                sku_details = [
                    SkuDetail(sku_id=sku.id, option_id=x.option_id, value_id=x.id)
                    for x in values
                ]
                s.add_all(sku_details)

    return json_response()


#
# Functions
#
