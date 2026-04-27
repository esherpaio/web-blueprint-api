from flask import abort
from sqlalchemy.orm.session import Session
from web.api import API, HttpText, json_response
from web.auth import current_user
from web.database import conn
from web.database.model import Billing, Cart, Order
from werkzeug import Response

from bp_api import api_bp

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
        Billing.is_default,
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
        Billing.is_default,
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
        Billing.is_default,
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


@api_bp.post("/billings")
def post_billings() -> Response:
    api = BillingAPI()
    api.validate_request()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = api.model()
        set_user(s, data, model)
        clear_default(s, data, model)
        api.insert(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.get("/billings/<int:billing_id>")
def get_billings_id(billing_id: int) -> Response:
    api = BillingAPI()
    api.validate_request()
    with conn.begin() as s:
        filters = {Billing.user_id == current_user.id}
        model: Billing = api.get(s, billing_id, *filters)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.patch("/billings/<int:billing_id>")
def patch_billings_id(billing_id: int) -> Response:
    api = BillingAPI()
    api.validate_request()
    data = api.gen_data(api.patch_columns)
    with conn.begin() as s:
        filters = {Billing.user_id == current_user.id}
        model: Billing = api.get(s, billing_id, *filters)
        val_order(s, data, model)
        clear_default(s, data, model)
        api.update(s, data, model)
        set_cart(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


#
# Functions
#


def set_user(s: Session, data: dict, model: Billing) -> None:
    model.user_id = current_user.id


def clear_default(s: Session, data: dict, model: Billing) -> None:
    """Demote the user's existing default before this row becomes the new default.

    Must run before insert/update; otherwise the partial unique index
    (one default per user) would reject the flush with a 409.
    """
    if not data.get("is_default"):
        return
    q = s.query(Billing).filter(
        Billing.user_id == current_user.id,
        Billing.is_default.is_(True),
    )
    if model.id is not None:
        q = q.filter(Billing.id != model.id)
    q.update({Billing.is_default: False}, synchronize_session=False)
    s.flush()


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
