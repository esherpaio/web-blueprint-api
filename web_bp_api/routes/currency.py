from web.api import API, json_response
from web_bp_api import api_bp
from web.auth import authorize
from web.database import conn
from web.database.model import Currency, UserRoleLevel
from werkzeug import Response

#
# Configuration
#


class CurrencyAPI(API):
    model = Currency
    post_columns = {
        Currency.code,
        Currency.rate,
        Currency.symbol,
    }
    get_columns = {
        Currency.code,
        Currency.rate,
        Currency.symbol,
        Currency.id,
    }


#
# Endpoints
#


@api_bp.post("/currencies")
@authorize(UserRoleLevel.ADMIN)
def post_currencies() -> Response:
    api = CurrencyAPI()
    data = api.gen_data(api.post_columns)
    with conn.begin() as s:
        model = api.model()
        api.insert(s, data, model)
        resource = api.gen_resource(s, model)
    return json_response(data=resource)


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


@api_bp.delete("/currencies/<int:currency_id>")
@authorize(UserRoleLevel.ADMIN)
def delete_currencies_id(currency_id: int) -> Response:
    api = CurrencyAPI()
    with conn.begin() as s:
        model: Currency = api.get(s, currency_id)
        api.delete(s, model)
    return json_response()


#
# Functions
#
