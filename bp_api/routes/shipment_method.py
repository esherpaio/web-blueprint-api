from decimal import Decimal

from sqlalchemy.orm import Session, joinedload
from web.api import API, HttpText, json_get, json_response
from web.api.utils.cart import get_shipment_methods_by_cart
from web.auth import authorize, current_user
from web.database import conn
from web.database.model import Cart, CartItem, ShipmentMethod, Sku, UserRoleLevel
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


@api_bp.post("/shipment-methods")
@authorize(UserRoleLevel.ADMIN)
def post_shipment_methods() -> Response:
    class_id, _ = json_get("class_id", int, nullable=False)
    name, _ = json_get("name", str, nullable=False)
    requires_billing_phone, _ = json_get("requires_billing_phone", bool, default=False)
    unit_price, _ = json_get("unit_price", Decimal, nullable=False)
    zone_id, _ = json_get("zone_id", int, nullable=False)

    with conn.begin() as s:
        # Insert shipment method
        shipment_method = ShipmentMethod(
            name=name,
            class_id=class_id,
            zone_id=zone_id,
            unit_price=unit_price,
            requires_billing_phone=requires_billing_phone,
        )
        s.add(shipment_method)

    return json_response()


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


@api_bp.patch("/shipment-methods/<int:shipment_method_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_shipment_methods_id(shipment_method_id: int) -> Response:
    name, has_name = json_get("name", str)
    requires_billing_phone, has_requires_billing_phone = json_get(
        "requires_billing_phone", bool
    )
    unit_price, has_unit_price = json_get("unit_price", Decimal)

    with conn.begin() as s:
        # Get shipment method
        shipment_method = (
            s.query(ShipmentMethod).filter_by(id=shipment_method_id).first()
        )
        if not shipment_method:
            return json_response(404, HttpText.HTTP_404)

        # Update shipment method
        if has_name:
            shipment_method.name = name
        if has_unit_price:
            shipment_method.unit_price = unit_price
        if has_requires_billing_phone:
            shipment_method.requires_billing_phone = requires_billing_phone

    return json_response()


@api_bp.delete("/shipment-methods/<int:shipment_method_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_shipment_methods_id(shipment_method_id: int) -> Response:
    with conn.begin() as s:
        # Delete shipment method
        shipment_method = (
            s.query(ShipmentMethod).filter_by(id=shipment_method_id).first()
        )
        if shipment_method is None:
            return json_response(404, HttpText.HTTP_404)
        shipment_method.is_deleted = True

    return json_response()


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
