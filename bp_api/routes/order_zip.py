import gc
from collections.abc import Iterator
from zipfile import ZIP_DEFLATED, ZipFile

from flask import request
from fpdf.image_datastructures import ImageCache
from web.auth import authorize
from web.database import conn
from web.database.model import Order, UserRoleLevel
from web.logger import log
from werkzeug import Response

from bp_api import api_bp
from bp_api.routes.order_invoice import get_invoice_pdf
from bp_api.routes.order_refund import get_refund_pdf


class _ZipStream:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def write(self, data: bytes) -> int:
        self._buffer += data
        return len(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    def take(self) -> bytes:
        data = bytes(self._buffer)
        self._buffer.clear()
        return data


#
# Endpoints
#


@api_bp.get("/orders/zip")
@authorize(UserRoleLevel.ADMIN)
def get_orders_zip() -> Response:
    order_ids = sorted({int(id_) for id_ in request.args["order_ids"].split(",")})
    response = Response(_gen_orders_zip(order_ids), mimetype="application/zip")
    response.headers["Content-Disposition"] = "attachment; filename=orders.zip"
    response.headers["Cache-Control"] = "private, no-store"
    return response


#
# Functions
#


def _gen_orders_zip(order_ids: list[int]) -> Iterator[bytes]:
    stream = _ZipStream()
    image_cache = ImageCache()
    try:
        with (
            conn.begin() as s,
            ZipFile(stream, "w", compression=ZIP_DEFLATED) as zip_file,
        ):
            for order_id in order_ids:
                order = s.get(Order, order_id)
                if order is None:
                    continue
                if order.invoice:
                    content, filename = get_invoice_pdf(
                        s,
                        order.id,
                        order.invoice.id,
                        image_cache=image_cache,
                    )
                    zip_file.writestr(filename, content)
                for refund in order.refunds:
                    content, filename = get_refund_pdf(
                        s,
                        order.id,
                        refund.id,
                        image_cache=image_cache,
                    )
                    zip_file.writestr(filename, content)
                s.expunge_all()
                gc.collect()
                yield stream.take()
        yield stream.take()
    except Exception:
        log.error("Failed to stream orders zip", exc_info=True)
        raise
