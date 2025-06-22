import uuid
from enum import StrEnum

from web.api import HttpText, json_get, json_response
from web.app.urls import parse_url, url_for
from web.config import config
from web.database import conn
from web.database.model import User, Verification
from web.i18n import _
from web.mail import mail
from web.mail.enum import MailEvent
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


class Text(StrEnum):
    ACTIVATION_CHECK = _("API_USER_ACTIVATION_CHECK")
    ACTIVATION_SUCCESS = _("API_USER_ACTIVATION_SUCCESS")
    VERIFICATION_FAILED = _("API_USER_VERIFICATION_FAILED")


#
# Endpoints
#


@api_bp.post("/users/<int:user_id>/activation")
def post_users_id_activation(user_id: int) -> Response:
    with conn.begin() as s:
        # Get user
        user = s.query(User).filter_by(id=user_id).first()
        if not user:
            return json_response(404, HttpText.HTTP_404)

        # Insert verification
        verification_key = str(uuid.uuid4())
        verification = Verification(user_id=user.id, key=verification_key)
        s.add(verification)
        s.flush()

        # Send email
        verification_url = parse_url(
            config.ENDPOINT_LOGIN,
            _func=url_for,
            _external=True,
            verification_key=verification.key,
        )
        mail.trigger_events(
            s,
            MailEvent.USER_REQUEST_VERIFICATION,
            email=user.email,
            verification_url=verification_url,
        )

    return json_response(200, message=Text.ACTIVATION_CHECK)


@api_bp.patch("/users/<int:user_id>/activation")
def patch_users_id_activation(user_id: int) -> Response:
    verification_key, _ = json_get("verification_key", str)

    with conn.begin() as s:
        # Get user
        user = s.query(User).filter_by(id=user_id).first()
        if not user:
            return json_response(404, HttpText.HTTP_404)

        # Check verification
        verification = s.query(Verification).filter_by(key=verification_key).first()
        if verification is None:
            return json_response(401, Text.VERIFICATION_FAILED)
        if not verification.is_valid:
            return json_response(401, Text.VERIFICATION_FAILED)
        if verification.user_id != user_id:
            return json_response(401, Text.VERIFICATION_FAILED)

        # Update activation
        user.is_active = True
        s.delete(verification)

    return json_response(200, message=Text.ACTIVATION_SUCCESS)


#
# Functions
#
