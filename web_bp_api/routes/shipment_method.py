from decimal import Decimal

from sqlalchemy import false, or_
from sqlalchemy.orm import Session, joinedload
from web.api import API, HttpText, json_get, json_response
from web.auth import authorize, current_user
from web.database import conn
from web.database.model import (
    Cart,
    CartItem,
    ShipmentClass,
    ShipmentMethod,
    ShipmentZone,
    Sku,
    UserRoleLevel,
)
from web.locale import current_locale
from werkzeug import Response

from web_bp_api import api_bp

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
        ShipmentMethod.phone_required,
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
    phone_required, _ = json_get("phone_required", bool, default=False)
    unit_price, _ = json_get("unit_price", Decimal, nullable=False)
    zone_id, _ = json_get("zone_id", int, nullable=False)

    with conn.begin() as s:
        # Insert shipment method
        shipment_method = ShipmentMethod(
            name=name,
            class_id=class_id,
            zone_id=zone_id,
            unit_price=unit_price,
            phone_required=phone_required,
        )
        s.add(shipment_method)

    return json_response()


@api_bp.get("/shipment-methods")
def get_shipment_methods() -> Response:
    api = ShipmentMethodAPI()
    data = api.gen_query_data(api.get_filters)
    with conn.begin() as s:
        models = set_shipment_methods(s, data, [])
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
    phone_required, has_phone_required = json_get("phone_required", bool)
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
        if has_phone_required:
            shipment_method.phone_required = phone_required

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


def set_shipment_methods(
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

    # Get all possible shipment class ids
    shipment_class_ids = []
    for item in cart.items:
        shipment_class_id = item.sku.product.shipment_class_id
        if shipment_class_id is not None:
            shipment_class_ids.append(shipment_class_id)

    # Determine the shipment class
    shipment_class = (
        s.query(ShipmentClass)
        .filter(
            ShipmentClass.id.in_(shipment_class_ids),
            ShipmentClass.is_deleted == false(),
        )
        .order_by(ShipmentClass.order)
        .first()
    )

    # Get country_id and region_id
    if cart.shipping:
        country_id = cart.shipping.country_id
        region_id = cart.shipping.country.region_id
    else:
        # NOTE(Stan): Not sure if we should do this
        country_id = current_locale.country.id
        region_id = current_locale.country.region_id

    # Determine the shipment zone
    shipment_zone = (
        s.query(ShipmentZone)
        .filter(
            or_(
                ShipmentZone.country_id == country_id,
                ShipmentZone.region_id == region_id,
            ),
            ShipmentZone.is_deleted == false(),
        )
        .order_by(ShipmentZone.order)
        .first()
    )

    # Get shipment methods
    if shipment_zone and shipment_class:
        shipment_methods = (
            s.query(ShipmentMethod)
            .filter_by(
                class_id=shipment_class.id,
                zone_id=shipment_zone.id,
                is_deleted=False,
            )
            .order_by(ShipmentMethod.unit_price)
            .all()
        )
    else:
        shipment_methods = []
    return shipment_methods
