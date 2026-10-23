from web.api import API, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import AppSettings, UserRoleLevel
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class SettingsAPI(API):
    model = AppSettings
    get_columns = {
        AppSettings.banner,
        AppSettings.cached_at,
    }


#
# Endpoints
#


@api_bp.get("/settings")
@authorize(UserRoleLevel.ADMIN)
def get_settings() -> Response:
    api = SettingsAPI()
    with conn.begin() as s:
        model: AppSettings = api.get(s, None)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)
