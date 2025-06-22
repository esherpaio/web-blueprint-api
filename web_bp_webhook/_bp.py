from flask import Blueprint

webhook_v1_bp = Blueprint(
    name="webhook_v1",
    import_name=__name__,
    url_prefix="/webhook/v1",
)
