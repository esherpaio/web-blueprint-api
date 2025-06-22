from datetime import datetime, timezone

from sqlalchemy.orm import Session
from web.api import API, json_response
from web.app.blueprint.api_v1 import api_v1_bp
from web.auth import authorize
from web.database import conn
from web.database.model import AppSettings, UserRoleLevel
from werkzeug import Response

#
# Configuration
#


class SettingsAPI(API):
    model = AppSettings
    patch_columns = {
        AppSettings.banner,
        AppSettings.cached_at,
    }
    get_columns = {
        AppSettings.banner,
        AppSettings.cached_at,
    }


#
# Endpoints
#


@api_v1_bp.get("/settings")
@authorize(UserRoleLevel.ADMIN)
def get_settings() -> Response:
    api = SettingsAPI()
    with conn.begin() as s:
        model: AppSettings = api.get(s, None)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_v1_bp.patch("/settings")
@authorize(UserRoleLevel.ADMIN)
def patch_settings() -> Response:
    api = SettingsAPI()
    data = api.gen_data(api.patch_columns)
    with conn.begin() as s:
        model: AppSettings = api.get(s, None)
        set_cache(s, data, model)
        api.update(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


#
# Functions
#


def set_cache(s: Session, data: dict, model: AppSettings) -> None:
    if "cached_at" in data:
        data["cached_at"] = datetime.now(timezone.utc).isoformat()
