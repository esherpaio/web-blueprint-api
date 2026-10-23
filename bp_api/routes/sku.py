from web.api import API, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Sku, UserRoleLevel
from werkzeug import Response

from bp_api import api_bp

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


#
# Functions
#
