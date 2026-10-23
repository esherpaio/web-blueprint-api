from web.api import API, json_response
from web.database import conn
from web.database.model import Language
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class LanguageAPI(API):
    model = Language
    get_columns = {
        Language.code,
        Language.in_sitemap,
        Language.name,
    }


#
# Endpoints
#


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


#
# Functions
#
