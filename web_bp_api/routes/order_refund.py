from decimal import Decimal
from enum import StrEnum

from web.api import HttpText, json_get, json_response
from web.api.utils.mollie import Mollie
from web_bp_api import api_bp
from web.auth import authorize
from web.database import conn
from web.database.model import Order, Refund, UserRoleLevel
from web.i18n import _
from web.mail import mail
from web.mail.enum import MailEvent
from werkzeug import Response

#
# Configuration
#


class Text(StrEnum):
    INVOICE_NOT_FOUND = _("API_ORDER_REFUND_INVOICE_NOT_FOUND")
    PAYMENT_INCOMPLETE = _("API_ORDER_REFUND_PAYMENT_INCOMPLETE")
    REFUND_NOT_ALLOWED = _("API_ORDER_REFUND_NOT_ALLOWED")
    REFUND_TOO_HIGH = _("API_ORDER_REFUND_TOO_HIGH")


#
# Endpoints
#


@api_bp.post("/orders/<int:order_id>/refunds")
@authorize(UserRoleLevel.ADMIN)
def post_orders_id_refund(order_id: int) -> Response:
    price, _ = json_get("total_price", Decimal, nullable=False)

    with conn.begin() as s:
        # Get order
        order = s.query(Order).filter_by(id=order_id).first()
        if not order:
            return json_response(404, HttpText.HTTP_404)

        # Check if an invoice exists
        if not order.invoice:
            return json_response(400, Text.INVOICE_NOT_FOUND)

        # Check if the order has a Mollie ID
        if not order.mollie_id:
            return json_response(404, Text.PAYMENT_INCOMPLETE)

        # Check if Mollie allows a refund
        mollie = Mollie()
        mollie_payment = mollie.payments.get(order.mollie_id)
        if not mollie_payment.can_be_refunded():
            return json_response(404, Text.REFUND_NOT_ALLOWED)

        # Insert refund
        if price > order.remaining_refund_amount:
            price = order.remaining_refund_amount
        price_vat = round(price * order.vat_rate, 2)
        refund_price = abs(price) * -1
        refund = Refund(order_id=order.id, total_price=refund_price)
        s.add(refund)
        s.flush()

        # Create Mollie refund
        mollie_payment = mollie.payments.get(order.mollie_id)
        mollie_refund = mollie_payment.refunds.create(
            {"amount": mollie.gen_amount(price_vat, order.currency_code)}
        )
        refund.mollie_id = mollie_refund.id
        s.flush()

        # Send email
        mail.trigger_events(
            s,
            MailEvent.ORDER_REFUNDED,
            order_id=order.id,
            refund_id=refund.id,
            billing_email=order.billing.email,
        )

    return json_response()


#
# Functions
#
