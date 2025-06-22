import uuid
from enum import StrEnum

from sqlalchemy.orm import Session
from web.api import HttpText, json_get, json_response
from web_bp_api import api_bp
from web.app.urls import parse_url, url_for
from web.config import config
from web.database import conn
from web.database.model import User, Verification
from web.i18n import _
from web.mail import mail
from web.mail.enum import MailEvent
from werkzeug import Response
from werkzeug.security import generate_password_hash

#
# Configuration
#


class Text(StrEnum):
    PASSWORD_LENGTH = _("API_USER_PASSWORD_LENGTH")
    PASSWORD_NO_MATCH = _("API_USER_PASSWORD_NO_MATCH")
    PASSWORD_REQUEST_SEND = _("API_USER_PASSWORD_REQUEST_SEND")
    PASSWORD_RESET_SUCCESS = _("API_USER_PASSWORD_RESET_SUCCESS")
    VERIFICATION_FAILED = _("API_USER_VERIFICATION_FAILED")


#
# Endpoints
#


@api_bp.post("/users/<int:user_id>/password")
def post_users_id_password(user_id: int) -> Response:
    with conn.begin() as s:
        # Get user
        user = s.query(User).filter_by(id=user_id).first()
        if user is None:
            return json_response(404, HttpText.HTTP_404)

        # Recover password
        recover_user_password(s, {}, user)

    return json_response(200, Text.PASSWORD_REQUEST_SEND)


@api_bp.patch("/users/<int:user_id>/password")
def patch_users_id_password(user_id: int) -> Response:
    password, _ = json_get("password", str)
    password_eval, _ = json_get("password_eval", str)
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

        # Check password
        if len(password) < 8:
            return json_response(400, Text.PASSWORD_LENGTH)
        if password != password_eval:
            return json_response(400, Text.PASSWORD_NO_MATCH)

        # Update password
        password_hash = generate_password_hash(password, "pbkdf2:sha256:1000000")
        user.password_hash = password_hash
        s.delete(verification)

    return json_response(200, Text.PASSWORD_RESET_SUCCESS)


#
# Functions
#


def recover_user_password(s: Session, data: dict, model: User) -> None:
    # Insert verification
    key = str(uuid.uuid4())
    verification = Verification(user_id=model.id, key=key)
    s.add(verification)
    s.flush()

    # Send email
    reset_url = parse_url(
        config.ENDPOINT_PASSWORD,
        _func=url_for,
        _external=True,
        verification_key=verification.key,
    )
    mail.trigger_events(
        s,
        MailEvent.USER_REQUEST_PASSWORD,
        email=model.email,
        reset_url=reset_url,
    )
