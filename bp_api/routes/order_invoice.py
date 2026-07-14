from flask import send_file
from web.api import HttpText, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Order, UserRoleLevel
from web.document import get_pdf_path
from web.document.object import gen_invoice_pdf
from web.i18n import _
from web.utils import remove_file
from werkzeug import Response

from bp_api import api_bp

#
# Endpoints
#


@api_bp.get("/orders/<int:order_id>/invoices/<int:invoice_id>/pdf")
@authorize(UserRoleLevel.ADMIN)
def get_orders_id_invoices_id_pdf(order_id: int, invoice_id: int) -> Response:
    with conn.begin() as s:
        order = s.query(Order).filter_by(id=order_id).first()
        if not order or not order.invoice or order.invoice.id != invoice_id:
            return json_response(404, HttpText.HTTP_404)
        invoice = order.invoice
        pdf = gen_invoice_pdf(s, order, invoice)
        pdf_name = _("PDF_INVOICE_FILENAME", invoice_number=invoice.number)
        pdf_path = get_pdf_path(pdf_name)
        pdf.output(pdf_path)
    remove_file(pdf_path, delay_s=20)
    return send_file(pdf_path, as_attachment=True, download_name=pdf_name)
