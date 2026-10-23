from web.api import API, json_response
from web.database import conn
from web.database.model import Currency
from werkzeug import Response

from bp_api import api_bp

#
# Configuration
#


class CurrencyAPI(API):
    model = Currency
    get_columns = {
        Currency.code,
        Currency.rate,
        Currency.symbol,
        Currency.id,
    }


#
# Endpoints
#


@api_bp.get("/currencies")
def get_currencies() -> Response:
    api = CurrencyAPI()
    with conn.begin() as s:
        models: list[Currency] = api.list_(s)
        resources = api.gen_resources(s, models)
    return json_response(data=resources)


@api_bp.get("/currencies/<int:currency_id>")
def get_currencies_id(currency_id: int) -> Response:
    api = CurrencyAPI()
    with conn.begin() as s:
        model: Currency = api.get(s, currency_id)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


#
# Functions
#
