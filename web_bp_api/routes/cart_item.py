from enum import StrEnum

from flask import abort
from sqlalchemy.orm.session import Session
from web.api import API, HttpText, json_response
from web.api.utils.cart import get_shipment_methods
from web.app.blueprint.api_v1 import api_v1_bp
from web.auth import current_user
from web.database import conn
from web.database.model import Cart, CartItem
from web.i18n import _
from web.utils import none_attrgetter
from werkzeug import Response

#
# Configuration
#


class Text(StrEnum):
    CART_ITEM_ADDED = _("API_CART_ITEM_ADDED")
    CART_ITEM_QUANTITY_ZERO = _("API_CART_ITEM_QUANTITY_ZERO")


class CartItemAPI(API):
    model = CartItem
    post_columns = {
        CartItem.quantity,
        CartItem.sku_id,
    }
    patch_columns = {
        CartItem.quantity,
    }
    get_columns = {
        CartItem.cart_id,
        CartItem.id,
        CartItem.quantity,
        CartItem.sku_id,
        "unit_price",
        "sku_name",
    }


#
# Endpoints
#


@api_v1_bp.post("/carts/<int:cart_id>/items")
def post_carts_id_items(cart_id: int) -> Response:
    api = CartItemAPI()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = upsert_cart_item(s, data, None)
        set_cart(s, data, None)
        resource = api.gen_resource(s, model)
    return json_response(message=Text.CART_ITEM_ADDED, data=resource)


@api_v1_bp.get("/carts/<int:cart_id>/items")
def get_carts_id_items(cart_id: int) -> Response:
    api = CartItemAPI()
    data = api.gen_path_data()
    with conn.begin() as s:
        authorize_cart(s, data, None)
        filters = {CartItem.cart_id == cart_id}
        models: list[CartItem] = api.list_(s, *filters)
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


@api_v1_bp.patch("/carts/<int:cart_id>/items/<int:cart_item_id>")
def patch_cart_id_items_id(cart_id: int, cart_item_id: int) -> Response:
    api = CartItemAPI()
    data = api.gen_data(api.patch_columns)
    with conn.begin() as s:
        authorize_cart(s, data, None)
        model: CartItem = api.get(s, cart_item_id)
        val_cart_item(s, data, model)
        api.update(s, data, model)
        set_cart(s, data, None)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_v1_bp.delete("/carts/<int:cart_id>/items/<int:cart_item_id>")
def delete_cart_id_items_id(cart_id: int, cart_item_id: int) -> Response:
    api = CartItemAPI()
    data = api.gen_path_data()
    with conn.begin() as s:
        authorize_cart(s, data, None)
        model: CartItem = api.get(s, cart_item_id)
        api.delete(s, model)
        set_cart(s, data, None)
    return json_response()


#
# Functions
#


def upsert_cart_item(s: Session, data: dict, model: None) -> CartItem:
    cart_id = data["cart_id"]
    sku_id = data["sku_id"]
    quantity = data.get("quantity", 1)

    filters = {Cart.user_id == current_user.id, Cart.id == cart_id}
    cart = s.query(Cart).filter(*filters).first()
    if cart is None:
        abort(json_response(404, HttpText.HTTP_404))
    else:
        for cart_item in cart.items:
            if cart_item.sku_id == sku_id:
                cart_item.quantity += quantity
                break
        else:
            cart_item = CartItem(cart_id=cart.id, sku_id=sku_id, quantity=quantity)
            cart.items.append(cart_item)

    s.flush()
    return cart_item


def set_cart(s: Session, data: dict, model: None) -> None:
    cart_id = data["cart_id"]
    cart = s.query(Cart).filter(Cart.id == cart_id).first()
    if cart is not None:
        shipment_methods = get_shipment_methods(s, cart)
        if shipment_methods:
            shipment_method = min(shipment_methods, key=none_attrgetter("unit_price"))
            cart.shipment_method_id = shipment_method.id
            cart.shipment_price = shipment_method.unit_price * cart.currency.rate
        else:
            cart.shipment_method_id = None
            cart.shipment_price = 0
        s.flush()


def val_cart_item(s: Session, data: dict, model: CartItem) -> None:
    if "quantity" in data and data["quantity"] <= 0:
        abort(json_response(400, Text.CART_ITEM_QUANTITY_ZERO))


def authorize_cart(s: Session, data: dict, model: None) -> Cart:
    cart_id = data["cart_id"]
    filters = {Cart.id == cart_id, Cart.user_id == current_user.id}
    cart = s.query(Cart).filter(*filters).first()
    if cart is None:
        abort(json_response(404, HttpText.HTTP_404))
    else:
        return cart
