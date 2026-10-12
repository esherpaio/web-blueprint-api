from tempfile import TemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from flask import request, send_file
from fpdf.image_datastructures import ImageCache
from web.auth import authorize
from web.database import conn
from web.database.model import Order, UserRoleLevel
from werkzeug import Response

from bp_api import api_bp
from bp_api.routes.order_invoice import get_invoice_pdf
from bp_api.routes.order_refund import get_refund_pdf


@api_bp.get("/orders/zip")
@authorize(UserRoleLevel.ADMIN)
def get_orders_zip() -> Response:
    order_ids = [int(id_) for id_ in request.args["order_ids"].split(",")]

    archive = TemporaryFile(mode="w+b")
    image_cache = ImageCache()
    try:
        with (
            conn.begin() as s,
            ZipFile(archive, "w", compression=ZIP_DEFLATED) as zip_file,
        ):
            orders = s.query(Order).filter(Order.id.in_(order_ids))
            for order in orders:
                if order.invoice:
                    content, filename = get_invoice_pdf(
                        s,
                        order.id,
                        order.invoice.id,
                        image_cache=image_cache,
                    )
                    zip_file.writestr(f"{filename}", content)
                for refund in order.refunds:
                    content, filename = get_refund_pdf(
                        s,
                        order.id,
                        refund.id,
                        image_cache=image_cache,
                    )
                    zip_file.writestr(f"{filename}", content)
        size = archive.tell()
        archive.seek(0)
        response = send_file(
            archive,
            mimetype="application/zip",
            as_attachment=True,
            download_name="orders.zip",
        )
        response.content_length = size
        response.headers["Cache-Control"] = "private, no-store"
        response.call_on_close(archive.close)
        return response
    except Exception:
        archive.close()
        raise
