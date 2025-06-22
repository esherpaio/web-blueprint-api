from enum import StrEnum

from flask import abort
from sqlalchemy.orm.session import Session
from web.api import API, json_response
from web.database import conn
from web.database.model import Verification
from web.i18n import _
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


class Text(StrEnum):
    VERIFICATION_INVALID = _("API_VERIFICATION_INVALID")


class VerificationAPI(API):
    model = Verification
    get_filters = {
        Verification.key,
    }
    get_columns = {
        Verification.id,
        Verification.key,
        Verification.user_id,
    }


#
# Endpoints
#


@api_bp.get("/verifications")
def get_verifications() -> Response:
    api = VerificationAPI()
    data = api.gen_query_data(api.get_filters)
    with conn.begin() as s:
        filters = api.gen_query_filters(data, required=True)
        models: list[Verification] = api.list_(s, *filters, limit=1)
        for model in models:
            val_verification(s, data, model)
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


#
# Functions
#


def val_verification(s: Session, data: dict, model: Verification) -> None:
    if not model.is_valid:
        abort(json_response(400, Text.VERIFICATION_INVALID))
