from enum import StrEnum

from flask import abort, g
from pyvat import is_vat_number_format_valid
from sqlalchemy.orm.session import Session
from web.api import API, HttpText, json_response
from web.api.utils.cart import get_shipment_methods
from web.api.utils.mollie import Mollie
from web.auth import authorize, current_user
from web.database import conn
from web.database.model import (
    Billing,
    Cart,
    Order,
    OrderLine,
    OrderStatus,
    OrderStatusId,
    Shipping,
    UserRoleLevel,
)
from web.database.utils import copy_row
from web.i18n import _
from web.mail import mail
from web.mail.enum import MailEvent
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class Text(StrEnum):
    PHONE_REQUIRED = _("API_ORDER_PHONE_REQUIRED")
    STATE_REQUIRED = _("API_ORDER_STATE_REQUIRED")
    STATUS_INVALID = _("API_ORDER_STATUS_INVALID")
    VAT_INVALID = _("API_ORDER_VAT_INVALID")
    VAT_NO_CONNECTION = _("API_ORDER_VAT_NO_CONNECTION")
    VAT_REQUIRED = _("API_ORDER_VAT_REQUIRED")
    SHIPMENT_METHOD_REQUIRED = _("API_SHIPMENT_METHOD_REQUIRED")
    SHIPMENT_METHOD_INVALID = _("API_SHIPMENT_METHOD_INVALID")
    CANCEL_NOT_ALLOWED = _("API_ORDER_CANCEL_NOT_ALLOWED")


class OrderAPI(API):
    model = Order
    post_columns = {
        "cart_id",
        "trigger_mail",
    }
    get_columns = {
        Order.id,
    }
    patch_columns = {
        Order.status_id,
    }


#
# Endpoints
#


@api_bp.post("/orders")
def post_orders() -> Response:
    api = OrderAPI()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = api.model()
        get_cart(s, data, model)
        val_cart(s, data, model)
        set_order(s, data, model)
        api.insert(s, data, model)
        set_order_lines(s, data, model)
        mail_order(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.patch("/orders/<int:order_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_orders_id(order_id: int) -> Response:
    api = OrderAPI()
    data = api.gen_data(api.patch_columns)
    with conn.begin() as s:
        model: Order = api.get(s, order_id)
        val_status(s, data, model)
        api.update(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.delete("/orders/<int:order_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_orders_id(order_id: int) -> Response:
    api = OrderAPI()
    data = api.gen_path_data()
    with conn.begin() as s:
        model: Order = api.get(s, order_id)
        cancel_mollie(s, data, model)
    return json_response()


#
# Functions
#


def get_cart(s: Session, data: dict, model: Order) -> None:
    cart_id = data["cart_id"]
    filters = {Cart.id == cart_id, Cart.user_id == current_user.id}
    cart = s.query(Cart).filter(*filters).first()
    if cart is None:
        abort(json_response(404, HttpText.HTTP_404))
    g.cart = cart


def val_status(s: Session, data: dict, model: Order) -> None:
    order_statuses = s.query(OrderStatus).all()
    if data["status_id"] not in {x.id for x in model.next_statuses(order_statuses)}:
        abort(json_response(400, Text.STATUS_INVALID))


def val_cart(s: Session, data: dict, model: Order) -> None:
    cart = g.cart
    # Check shipment method
    shipment_methods = get_shipment_methods(s, cart)
    if shipment_methods:
        if cart.shipment_method_id is None:
            abort(json_response(400, Text.SHIPMENT_METHOD_REQUIRED))
        shipment_method_ids = {x.id for x in shipment_methods}
        if cart.shipment_method_id not in shipment_method_ids:
            abort(json_response(400, Text.SHIPMENT_METHOD_INVALID))
    # Check phone required
    if cart.shipment_method is not None:
        if cart.shipment_method.requires_billing_phone:
            if cart.billing.phone is None:
                abort(json_response(400, Text.PHONE_REQUIRED))
    # Check VAT required in Europe
    if cart.billing.company is not None:
        if cart.billing.country.requires_billing_vat:
            if cart.billing.vat is None:
                abort(json_response(400, Text.VAT_REQUIRED))
    # Check VAT number
    if cart.billing.vat is not None:
        vat_parsed = "".join(x for x in cart.billing.vat if x.isalnum())
        is_valid = is_vat_number_format_valid(vat_parsed, cart.billing.country.code)
        if not is_valid:
            abort(json_response(400, Text.VAT_INVALID))
    # Check state
    if cart.billing.country.requires_billing_state:
        if cart.billing.state is None:
            abort(json_response(400, Text.STATE_REQUIRED))


def set_order(s: Session, data: dict, model: Order) -> None:
    # get cart from g object
    cart = g.cart
    # set detached values
    if cart.coupon is not None:
        model.coupon_amount = cart.coupon.amount
        model.coupon_code = cart.coupon.code
        model.coupon_rate = cart.coupon.rate
    if cart.shipment_method is not None:
        model.shipment_name = cart.shipment_method.name
    # copy billing and shipping
    model.billing = copy_row(s, cart.billing, Billing())
    model.shipping = copy_row(s, cart.shipping, Shipping())
    # set values
    model.billing_id = cart.billing_id
    model.currency_code = cart.currency.code
    model.shipment_price = cart.shipment_price
    model.shipping_id = cart.shipping_id
    model.total_price = cart.total_price
    model.vat_rate = cart.vat_rate
    model.vat_reverse = cart.vat_reverse
    model.user_id = current_user.id
    model.status_id = OrderStatusId.PENDING


def set_order_lines(s: Session, data: dict, model: Order) -> None:
    cart = g.cart
    order_lines = []
    for cart_item in cart.items:
        order_line = OrderLine()
        order_line.order_id = model.id
        order_line.sku_id = cart_item.sku_id
        order_line.quantity = cart_item.quantity
        order_line.total_price = cart_item.total_price
        order_lines.append(order_line)
    s.add_all(order_lines)
    s.flush()
    g.order_lines = order_lines


def mail_order(s: Session, data: dict, model: Order) -> None:
    if data.get("trigger_mail", True):
        mail.trigger_events(
            s,
            MailEvent.ORDER_RECEIVED,
            order_id=model.id,
            billing_email=model.billing.email,
            shipping_email=model.shipping.email,
        )


def cancel_mollie(s: Session, data: dict, model: Order) -> None:
    mollie = Mollie()
    mollie_payment = mollie.payments.get(model.mollie_id)
    if mollie_payment.is_canceled():
        return
    if not mollie_payment.is_cancelable:
        abort(400, Text.CANCEL_NOT_ALLOWED)
    mollie.payments.delete(model.mollie_id)
    model.status_id = OrderStatusId.COMPLETED
