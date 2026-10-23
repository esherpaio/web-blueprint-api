from web.api import API, json_response
from web.database import conn
from web.database.model import Country
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class CountryAPI(API):
    model = Country
    get_columns = {
        Country.code,
        Country.in_sitemap,
        Country.name,
        Country.id,
        Country.allows_shipping,
        Country.currency_id,
        Country.region_id,
    }


#
# Endpoints
#


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


#
# Functions
#
