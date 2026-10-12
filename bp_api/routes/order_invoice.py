from io import BytesIO

from flask import abort, send_file
from fpdf.image_datastructures import ImageCache
from sqlalchemy.orm import Session
from web.api import HttpText, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Order, UserRoleLevel
from web.document.object import gen_invoice_pdf
from web.i18n import _
from werkzeug import Response
from werkzeug.utils import secure_filename

from bp_api import api_bp

#
# Endpoints
#


@api_bp.get("/orders/<int:order_id>/invoices/<int:invoice_id>/pdf")
@authorize(UserRoleLevel.ADMIN)
def get_orders_id_invoices_id_pdf(order_id: int, invoice_id: int) -> Response:
    with conn.begin() as s:
        content, filename = get_invoice_pdf(s, order_id, invoice_id)
    response = send_file(
        BytesIO(content),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
    response.headers["Cache-Control"] = "private, no-store"
    return response


#
# Functions
#


def get_invoice_pdf(
    s: Session,
    order_id: int,
    invoice_id: int,
    *,
    image_cache: ImageCache | None = None,
) -> tuple[bytes, str]:
    order = s.get(Order, order_id)
    if not order or not order.invoice or order.invoice.id != invoice_id:
        abort(json_response(404, HttpText.HTTP_404))
    invoice = order.invoice
    pdf = gen_invoice_pdf(s, order, invoice, image_cache=image_cache)
    filename = secure_filename(_("PDF_INVOICE_FILENAME", invoice_number=invoice.number))
    return bytes(pdf.output()), filename
