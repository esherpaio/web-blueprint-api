from web.api import HttpText, json_get, json_response
from web_bp_api import api_bp
from web.auth import authorize
from web.database import conn
from web.database.model import Order, OrderStatusId, Shipment, UserRoleLevel
from web.mail.enum import MailEvent
from web.mail.mail import mail
from werkzeug import Response

#
# Configuration
#


#
# Endpoints
#


@api_bp.post("/orders/<int:order_id>/shipments")
@authorize(UserRoleLevel.ADMIN)
def post_orders_id_shipments(order_id: int) -> Response:
    url, _ = json_get("url", str, nullable=False)

    with conn.begin() as s:
        # Get order
        order = s.query(Order).filter_by(id=order_id).first()
        if order is None:
            return json_response(404, HttpText.HTTP_404)

        # Insert shipment
        shipment = Shipment(order_id=order_id, url=url)
        s.add(shipment)
        s.flush()

        # Update order
        order.status_id = OrderStatusId.COMPLETED
        s.flush()

        # Send email
        mail.trigger_events(
            s,
            MailEvent.ORDER_SHIPPED,
            order_id=order_id,
            shipment_url=url,
            billing_email=order.billing.email,
            shipping_email=order.shipping.email,
            shipping_address=order.shipping.full_address,
        )

    return json_response()


#
# Functions
#
