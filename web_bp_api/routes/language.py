from web.api import API, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Language, UserRoleLevel
from werkzeug import Response

from web_bp_api import api_bp

#
# Configuration
#


class LanguageAPI(API):
    model = Language
    post_columns = {
        Language.code,
        Language.in_sitemap,
        Language.name,
    }
    get_columns = {
        Language.code,
        Language.in_sitemap,
        Language.name,
    }


#
# Endpoints
#


@api_bp.post("/languages")
@authorize(UserRoleLevel.ADMIN)
def post_languages() -> Response:
    api = LanguageAPI()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = api.model()
        api.insert(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.get("/languages")
def get_languages() -> Response:
    api = LanguageAPI()
    with conn.begin() as s:
        models: list[Language] = api.list_(s)
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


@api_bp.get("/languages/<int:language_id>")
def get_languages_id(language_id: int) -> Response:
    api = LanguageAPI()
    with conn.begin() as s:
        model: Language = api.get(s, language_id)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.delete("/languages/<int:language_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_languages_id(language_id: int) -> Response:
    api = LanguageAPI()
    with conn.begin() as s:
        model: Language = api.get(s, language_id)
        api.delete(s, model)
    return json_response()


#
# Functions
#
