from sqlalchemy.orm import Session, joinedload
from web.api import API, json_response
from web.api.utils.cart import get_shipment_methods_by_cart
from web.auth import current_user
from web.database import conn
from web.database.model import Cart, CartItem, ShipmentMethod, Sku
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class ShipmentMethodAPI(API):
    model = ShipmentMethod
    get_filters = {
        "cart_id",
    }
    get_columns = {
        ShipmentMethod.id,
        ShipmentMethod.name,
        ShipmentMethod.requires_billing_phone,
        ShipmentMethod.unit_price,
        ShipmentMethod.class_id,
        ShipmentMethod.zone_id,
    }


#
# Endpoints
#


@api_bp.get("/shipment-methods")
def get_shipment_methods() -> Response:
    api = ShipmentMethodAPI()
    data = api.gen_query_data(api.get_filters)
    with conn.begin() as s:
        models = _get_shipment_methods(s, data, [])
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


@api_bp.get("/shipment-methods/<int:shipment_method_id>")
def get_shipment_methods_id(shipment_method_id: int) -> Response:
    api = ShipmentMethodAPI()
    with conn.begin() as s:
        model: ShipmentMethod = api.get(s, shipment_method_id)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


#
# Functions
#


def _get_shipment_methods(
    s: Session,
    data: dict,
    model: list[ShipmentMethod],
) -> list[ShipmentMethod]:
    # Get cart
    cart_id = data["cart_id"]
    cart = (
        s.query(Cart)
        .options(
            joinedload(Cart.currency),
            joinedload(Cart.items),
            joinedload(Cart.items, CartItem.cart),
            joinedload(Cart.items, CartItem.sku),
            joinedload(Cart.items, CartItem.sku, Sku.product),
        )
        .filter_by(id=cart_id, user_id=current_user.id)
        .first()
    )
    if cart is None:
        return []
    return get_shipment_methods_by_cart(s, cart)
