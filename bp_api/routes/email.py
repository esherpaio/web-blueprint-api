import time
from enum import StrEnum

import requests
from sqlalchemy import null, true
from web.api import json_get, json_response
from web.database import conn
from web.database.model import User
from web.i18n import _
from web.logger import log
from web.mail import mail
from web.mail.enum import MailEvent
from web.setup import config
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class Text(StrEnum):
    CONTACT_SUCCESS = _("API_MAIL_CONTACT_SUCCESS")
    EVENT_ID_INVALID = _("API_MAIL_INVALID_EVENT_ID")
    MAIL_ERROR = _("API_MAIL_ERROR")
    TOO_MANY_EMAILS = _("API_MAIL_TOO_MANY")
    CONTACT_ADMIN = _("API_MAIL_CONTACT_ADMIN")


#
# Endpoints
#


@api_bp.post("/emails")
def post_emails() -> Response:
    event_id, _ = json_get("event_id", str, nullable=False)
    turnstile_token, has_turnstile_token = json_get("turnstile_token", str)
    data, _ = json_get("data", dict, default={})

    if (
        config.TURNSTILE_SITE_KEY
        and config.TURNSTILE_SECRET_KEY
        and (not has_turnstile_token or not validate_turnstile(turnstile_token))
    ):
        return json_response(403, Text.MAIL_ERROR)

    with conn.begin() as s:
        # Inject emails for bulk email
        if event_id == MailEvent.WEBSITE_BULK:
            if not config.WORKER_ENABLED:
                return json_response(400, Text.CONTACT_ADMIN)
            if "emails" not in data:
                users = (
                    s.query(User)
                    .filter(
                        User.is_active == true(),
                        User.bulk_email == true(),
                        User.email != null(),
                    )
                    .all()
                )
                emails = set(user.email for user in users)
                if len(emails) > config.MAIL_MAX_RECEIVERS:
                    return json_response(400, Text.TOO_MANY_EMAILS)
                data["emails"] = list(emails)

        # Trigger email events
        result = mail.trigger_events(s, event_id, **data)

    if not result:
        return json_response(400, Text.MAIL_ERROR)
    return json_response(200, Text.CONTACT_SUCCESS)


#
# Functions
#


def validate_turnstile(token: str) -> bool:
    if not config.TURNSTILE_SITE_KEY or not config.TURNSTILE_SECRET_KEY:
        log.error("Turnstile keys not configured")
        return False

    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {"secret": config.TURNSTILE_SECRET_KEY, "response": token}

    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["success"]
    except requests.RequestException as e:
        log.warning(f"Turnstile validation error: {e}")
        time.sleep(5)  # Sleep to mitigate potential abuse
        return False
