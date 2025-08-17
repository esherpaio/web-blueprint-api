from enum import StrEnum

from sqlalchemy import null, true
from web.api import json_get, json_response
from web.database import conn
from web.database.model import User
from web.i18n import _
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
    event_id, _ = json_get("event_id", str)
    data, _ = json_get("data", dict, default={})

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
