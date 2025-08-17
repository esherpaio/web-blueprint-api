from decimal import Decimal
from typing import Any

from flask import abort
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import has_identity
from web.api import API, HttpText, json_response
from web.api.utils.cart import get_shipment_methods
from web.api.utils.vat import get_vat
from web.auth import current_user
from web.database import conn
from web.database.model import Billing, Cart, Coupon, Shipping
from web.locale import current_locale
from web.utils import none_attrgetter
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class CartAPI(API):
    model = Cart
    patch_columns = {
        Cart.billing_id,
        Cart.shipping_id,
        Cart.coupon_id,
        Cart.shipment_method_id,
        "coupon_code",
    }
    get_columns = {
        Cart.id,
        Cart.user_id,
        Cart.billing_id,
        Cart.shipping_id,
        Cart.coupon_id,
        Cart.currency_id,
        Cart.shipment_method_id,
        Cart.vat_rate,
        Cart.vat_reverse,
        "vat_percentage",
        "vat_amount",
        "items_count",
        "currency_code",
        "coupon_code",
        "subtotal_price",
        "subtotal_price_vat",
        "discount_price",
        "discount_price_vat",
        "shipment_price",
        "shipment_price_vat",
        "total_price",
        "total_price_vat",
    }


#
# Endpoints
#


@api_bp.post("/carts")
def post_carts() -> Response:
    api = CartAPI()
    data: dict[str, Any] = {}
    with conn.begin() as s:
        model = api.model()
        set_user(s, data, model)
        set_vat(s, data, model)
        api.insert(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.get("/carts")
def get_carts() -> Response:
    api = CartAPI()
    with conn.begin() as s:
        filters = {Cart.user_id == current_user.id}
        models: list[Cart] = api.list_(s, *filters, limit=1)
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


@api_bp.get("/carts/<int:cart_id>")
def get_carts_id(cart_id: int) -> Response:
    api = CartAPI()
    with conn.begin() as s:
        filters = {Cart.user_id == current_user.id}
        model: Cart = api.get(s, cart_id, *filters)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.patch("/carts/<int:cart_id>")
def patch_carts_id(cart_id: int) -> Response:
    api = CartAPI()
    data = api.gen_data(api.patch_columns)
    with conn.begin() as s:
        filters = {Cart.user_id == current_user.id}
        model: Cart = api.get(s, cart_id, *filters)
        set_vat(s, data, model)
        set_shipment(s, data, model)
        set_coupon(s, data, model)
        api.update(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.delete("/carts/<int:cart_id>")
def delete_carts_id(cart_id: int) -> Response:
    api = CartAPI()
    with conn.begin() as s:
        filters = {Cart.user_id == current_user.id}
        model: Cart = api.get(s, cart_id, *filters)
        api.delete(s, model)
    return json_response()


#
# Functions
#


def set_user(s: Session, data: dict, model: Cart) -> None:
    model.user_id = current_user.id


def set_vat(s: Session, data: dict, model: Cart) -> None:
    if "billing_id" in data:
        billing_id = data["billing_id"]
        billing = s.query(Billing).filter_by(id=billing_id).first()
    elif model.billing is not None:
        billing = model.billing
    else:
        billing = None

    if "shipping_id" in data:
        shipping_id = data["shipping_id"]
        shipping = s.query(Shipping).filter_by(id=shipping_id).first()
    elif model.shipping is not None:
        shipping = model.shipping
    else:
        shipping = None

    if billing is not None:
        country_code = billing.country.code
        is_business = billing.company is not None
        currency_id = billing.country.currency_id
    elif shipping is not None:
        country_code = shipping.country.code
        is_business = shipping.company is not None
        currency_id = shipping.country.currency_id
    else:
        country_code = current_locale.country.code
        is_business = False
        currency_id = current_locale.currency.id

    vat_rate, vat_reverse = get_vat(country_code, is_business)
    model.currency_id = currency_id
    model.vat_rate = vat_rate
    model.vat_reverse = vat_reverse
    s.flush()
    if has_identity(model):
        s.expire(model)


def set_shipment(s: Session, data: dict, model: Cart) -> None:
    if "shipment_method_id" in data:
        shipment_method_id = data["shipment_method_id"]
    elif model.shipment_method is not None:
        shipment_method_id = model.shipment_method_id
    else:
        shipment_method_id = None

    shipment_methods = get_shipment_methods(s, model)
    if shipment_method_id is not None:
        shipment_method = next(
            (
                shipment_method
                for shipment_method in shipment_methods
                if shipment_method.id == shipment_method_id
            ),
            None,
        )
    else:
        shipment_method = None

    if shipment_methods and shipment_method is None:
        shipment_method = min(
            shipment_methods,
            key=none_attrgetter("unit_price"),
        )

    if shipment_method is not None:
        model.shipment_method_id = shipment_method.id
        model.shipment_price = shipment_method.unit_price * model.currency.rate
    else:
        model.shipment_method_id = None
        model.shipment_price = Decimal("0.00")

    s.flush()
    if has_identity(model):
        s.expire(model)


def set_coupon(s: Session, data: dict, model: Cart) -> None:
    if "coupon_code" in data:
        coupon_code = data["coupon_code"]
        if coupon_code is None:
            coupon_id = None
        else:
            coupon = (
                s.query(Coupon).filter_by(code=coupon_code, is_deleted=False).first()
            )
            if coupon is None:
                abort(json_response(400, HttpText.HTTP_400))
            else:
                coupon_id = coupon.id
        model.coupon_id = coupon_id
