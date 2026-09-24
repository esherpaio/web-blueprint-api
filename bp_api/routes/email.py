from enum import StrEnum

import requests
from web.api import json_get, json_response
from web.database import conn
from web.i18n import _
from web.logger import log
from web.mail import mail
from web.setup import config
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


TURNSTILE_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class Text(StrEnum):
    CONTACT_SUCCESS = _("API_MAIL_CONTACT_SUCCESS")
    EVENT_ID_INVALID = _("API_MAIL_INVALID_EVENT_ID")
    MAIL_ERROR = _("API_MAIL_ERROR")


#
# Endpoints
#


@api_bp.post("/emails")
def post_emails() -> Response:
    event_id, _ = json_get("event_id", str, nullable=False)
    turnstile_token, _ = json_get("turnstile_token", str)
    data, _ = json_get("data", dict, default={})

    if event_id in (config.TURNSTILE_EVENT_IDS or []):
        if not validate_turnstile(turnstile_token):
            return json_response(403, Text.MAIL_ERROR)

    with conn.begin() as s:
        result = mail.trigger_events(s, event_id, **data)
    if not result:
        return json_response(400, Text.MAIL_ERROR)
    return json_response(200, Text.CONTACT_SUCCESS)


#
# Functions
#


def validate_turnstile(token: object) -> bool:
    if not isinstance(token, str) or not token.strip() or len(token) > 2048:
        return False
    if not config.TURNSTILE_SITE_KEY or not config.TURNSTILE_SECRET_KEY:
        log.error("Turnstile keys not configured")
        return False

    data = {"secret": config.TURNSTILE_SECRET_KEY, "response": token}
    try:
        response = requests.post(TURNSTILE_URL, data=data, timeout=10)
        response.raise_for_status()
        data = response.json()
        return isinstance(data, dict) and data.get("success") is True
    except (requests.RequestException, ValueError) as e:
        log.warning(f"Turnstile validation error: {type(e).__name__}")
        return False
