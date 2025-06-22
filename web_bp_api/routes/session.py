from enum import StrEnum

from google.auth.transport import requests
from google.oauth2 import id_token
from web.api import json_get, json_response
from web.api.utils.cart import transfer_cart
from web_bp_api import api_bp
from web.auth import jwt_login, jwt_logout
from web.config import config
from web.database import conn
from web.database.model import User, UserRoleId
from web.i18n import _
from werkzeug import Response
from werkzeug.security import check_password_hash

from .user_password import recover_user_password

#
# Configuration
#


class Text(StrEnum):
    CHECK_DETAILS = _("API_SESSION_CHECK_DETAILS")
    CHECK_ACTIVATION = _("API_SESSION_CHECK_ACTIVATION")
    CHECK_PASSWORD = _("API_SESSION_CHECK_PASSWORD")
    GOOGLE_INVALID = _("API_SESSION_GOOGLE_INVALID")


#
# Endpoints
#


@api_bp.post("/sessions")
@transfer_cart
def post_sessions() -> Response:
    email, _ = json_get("email", str, nullable=False)
    password, _ = json_get("password", str, nullable=False)
    remember, _ = json_get("remember", bool, default=False)

    # Get user
    with conn.begin() as s:
        user = s.query(User).filter_by(email=email.lower()).first()

    # Validate user
    if user is None:
        return json_response(400, Text.CHECK_DETAILS)
    if not user.is_active:
        return json_response(400, Text.CHECK_ACTIVATION)
    if not user.password_hash:
        with conn.begin() as s:
            recover_user_password(s, {}, user)
        return json_response(400, Text.CHECK_PASSWORD)
    if not check_password_hash(user.password_hash, password):
        return json_response(400, Text.CHECK_DETAILS)

    # Login user
    jwt_login(user.id)
    return json_response()


@api_bp.delete("/sessions")
def delete_sessions() -> Response:
    # Logout user
    jwt_logout()
    return json_response()


@api_bp.post("/sessions/google")
@transfer_cart
def post_sessions_google() -> Response:
    token_id, _ = json_get("token_id", str, nullable=False)
    token = id_token.verify_oauth2_token(
        token_id, requests.Request(), audience=config.GOOGLE_CLIENT_ID
    )
    email = token.get("email")
    if email is None:
        return json_response(400, Text.GOOGLE_INVALID)

    # Get or add user
    with conn.begin() as s:
        user = s.query(User).filter_by(email=email.lower()).first()
        if user is not None and not user.is_active:
            user.is_active = True
        if user is None:
            user = User(email=email, is_active=True, role_id=UserRoleId.USER)
            s.add(user)

    # Login user
    jwt_login(user.id)
    return json_response()


#
# Functions
#
