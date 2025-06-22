from flask import abort
from sqlalchemy.orm.session import Session
from web.api import API, HttpText, json_response
from web.app.blueprint.api_v1 import api_v1_bp
from web.auth import current_user
from web.database import conn
from web.database.model import Billing, Cart, Order
from werkzeug import Response

from .cart import set_shipment, set_vat

#
# Configuration
#


class BillingAPI(API):
    model = Billing
    post_columns = {
        Billing.address,
        Billing.city,
        Billing.company,
        Billing.country_id,
        Billing.email,
        Billing.first_name,
        Billing.last_name,
        Billing.phone,
        Billing.state,
        Billing.vat,
        Billing.zip_code,
    }
    patch_columns = {
        Billing.address,
        Billing.city,
        Billing.company,
        Billing.country_id,
        Billing.email,
        Billing.first_name,
        Billing.last_name,
        Billing.phone,
        Billing.state,
        Billing.vat,
        Billing.zip_code,
    }
    get_columns = {
        Billing.address,
        Billing.city,
        Billing.company,
        Billing.country_id,
        Billing.email,
        Billing.first_name,
        Billing.id,
        Billing.last_name,
        Billing.phone,
        Billing.state,
        Billing.user_id,
        Billing.vat,
        Billing.zip_code,
    }


#
# Endpoints
#


@api_v1_bp.post("/billings")
def post_billings() -> Response:
    api = BillingAPI()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = api.model()
        set_user(s, data, model)
        api.insert(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_v1_bp.get("/billings/<int:billing_id>")
def get_billings_id(billing_id: int) -> Response:
    api = BillingAPI()
    with conn.begin() as s:
        filters = {Billing.user_id == current_user.id}
        model: Billing = api.get(s, billing_id, *filters)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_v1_bp.patch("/billings/<int:billing_id>")
def patch_billings_id(billing_id: int) -> Response:
    api = BillingAPI()
    data = api.gen_data(api.patch_columns)
    with conn.begin() as s:
        filters = {Billing.user_id == current_user.id}
        model: Billing = api.get(s, billing_id, *filters)
        val_order(s, data, model)
        api.update(s, data, model)
        set_cart(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


#
# Functions
#


def set_user(s: Session, data: dict, model: Billing) -> None:
    model.user_id = current_user.id


def set_cart(s: Session, data: dict, model: Billing) -> None:
    carts = s.query(Cart).filter_by(billing_id=model.id).all()
    for cart in carts:
        set_vat(s, data, cart)
        set_shipment(s, data, cart)


def val_order(s: Session, data: dict, model: Billing) -> None:
    filters = {Order.billing_id == model.id}
    order = s.query(Order).filter(*filters).first()
    if order is not None:
        abort(json_response(403, HttpText.HTTP_403))
