from web.api import API, json_response
from web.auth import authorize
from web.database import conn
from web.database.model import Country, UserRoleLevel
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class CountryAPI(API):
    model = Country
    post_columns = {
        Country.code,
        Country.in_sitemap,
        Country.name,
        Country.currency_id,
        Country.region_id,
    }
    patch_columns = {
        Country.state_required,
        Country.vat_required,
    }
    get_columns = {
        Country.code,
        Country.in_sitemap,
        Country.name,
        Country.id,
        Country.currency_id,
        Country.region_id,
    }


#
# Endpoints
#


@api_bp.post("/countries")
@authorize(UserRoleLevel.ADMIN)
def post_countries() -> Response:
    api = CountryAPI()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = api.model()
        api.insert(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.get("/countries")
def get_countries() -> Response:
    api = CountryAPI()
    with conn.begin() as s:
        models: list[Country] = api.list_(s, order_by=Country.name)
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


@api_bp.get("/countries/<int:country_id>")
def get_countries_id(country_id: int) -> Response:
    api = CountryAPI()
    with conn.begin() as s:
        model: Country = api.get(s, country_id)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.patch("/countries/<int:country_id>")
@authorize(UserRoleLevel.ADMIN)
def patch_countries_id(country_id: int) -> Response:
    api = CountryAPI()
    data = api.gen_data(api.patch_columns)
    with conn.begin() as s:
        model: Country = api.get(s, country_id)
        api.update(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


@api_bp.delete("/countries/<int:country_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_countries_id(country_id: int) -> Response:
    api = CountryAPI()
    with conn.begin() as s:
        model: Country = api.get(s, country_id)
        api.delete(s, model)
    return json_response()


#
# Functions
#
