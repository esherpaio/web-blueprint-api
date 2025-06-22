from flask import abort
from sqlalchemy.orm.session import Session
from web.api import API, HttpText, json_response
from web_bp_api import api_bp
from web.auth import current_user
from web.database import conn
from web.database.model import Cart, Order, Shipping
from werkzeug import Response

from .cart import set_shipment, set_vat

#
# Configuration
#


class ShippingAPI(API):
    model = Shipping
    post_columns = {
        Shipping.address,
        Shipping.city,
        Shipping.company,
        Shipping.country_id,
        Shipping.email,
        Shipping.first_name,
        Shipping.last_name,
        Shipping.phone,
        Shipping.state,
        Shipping.zip_code,
    }
    patch_columns = {
        Shipping.address,
        Shipping.city,
        Shipping.company,
        Shipping.country_id,
        Shipping.email,
        Shipping.first_name,
        Shipping.last_name,
        Shipping.phone,
        Shipping.state,
        Shipping.zip_code,
    }
    get_columns = {
        Shipping.address,
        Shipping.city,
        Shipping.company,
        Shipping.country_id,
        Shipping.email,
        Shipping.first_name,
        Shipping.id,
        Shipping.last_name,
        Shipping.phone,
        Shipping.state,
        Shipping.user_id,
        Shipping.zip_code,
    }


#
# Endpoints
#


@api_bp.post("/shippings")
def post_shippings() -> Response:
    api = ShippingAPI()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = api.model()
        set_user(s, data, model)
        api.insert(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.get("/shippings/<int:shipping_id>")
def get_shippings_id(shipping_id: int) -> Response:
    api = ShippingAPI()
    with conn.begin() as s:
        filters = {Shipping.user_id == current_user.id}
        model: Shipping = api.get(s, shipping_id, *filters)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.patch("/shippings/<int:shipping_id>")
def patch_shippings_id(shipping_id: int) -> Response:
    api = ShippingAPI()
    data = api.gen_data(api.patch_columns)
    with conn.begin() as s:
        filters = {Shipping.user_id == current_user.id}
        model: Shipping = api.get(s, shipping_id, *filters)
        val_order(s, data, model)
        api.update(s, data, model)
        set_cart(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


#
# Functions
#


def set_user(s: Session, data: dict, model: Shipping) -> None:
    model.user_id = current_user.id


def set_cart(s: Session, data: dict, model: Shipping) -> None:
    carts = s.query(Cart).filter_by(shipping_id=model.id).all()
    for cart in carts:
        set_vat(s, data, cart)
        set_shipment(s, data, cart)


def val_order(s: Session, data: dict, model: Shipping) -> None:
    filters = {Order.shipping_id == model.id}
    order = s.query(Order).filter(*filters).first()
    if order is not None:
        abort(json_response(403, HttpText.HTTP_403))
