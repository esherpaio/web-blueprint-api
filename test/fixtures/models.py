import pytest
from web.cache import cache_manager
from web.database import conn
from web.database.model import Country, Currency, Language, Region

#
# Currency
#


@pytest.fixture(scope="function")
def add_currency_eur(client):
    with conn.begin() as s:
        currency = Currency(code="EUR", rate=1, symbol="€")
        s.add(currency)
    cache_manager.update(force=True)
    return currency


@pytest.fixture(scope="function")
def add_currency_gbp(client):
    with conn.begin() as s:
        currency = Currency(code="GBP", rate=1, symbol="£")
        s.add(currency)
    cache_manager.update(force=True)
    return currency


#
# Region
#


@pytest.fixture(scope="function")
def add_region_europe(client):
    with conn.begin() as s:
        region = Region(name="Europe")
        s.add(region)
    cache_manager.update(force=True)
    return region


#
# Country
#


@pytest.fixture(scope="function")
def add_country_nl(client, add_currency_eur, add_region_europe):
    with conn.begin() as s:
        country = Country(
            code="NL",
            in_sitemap=False,
            name="the Netherlands",
            currency_id=add_currency_eur.id,
            region_id=add_region_europe.id,
        )
        s.add(country)
    cache_manager.update(force=True)
    return country


@pytest.fixture(scope="function")
def add_country_uk(client, add_currency_gbp, add_region_europe):
    with conn.begin() as s:
        country = Country(
            code="GB",
            in_sitemap=False,
            name="United Kingdom",
            currency_id=add_currency_gbp.id,
            region_id=add_region_europe.id,
        )
        s.add(country)
    cache_manager.update(force=True)
    return country


#
# Language
#


@pytest.fixture(scope="function")
def add_language_nl(client):
    with conn.begin() as s:
        language = Language(
            code="nl",
            in_sitemap=False,
            name="Dutch",
        )
        s.add(language)
    cache_manager.update(force=True)
    return language


#
# User
#


@pytest.fixture(scope="function")
def user_data():
    return {
        "email": "user@esherpa.io",
        "password": "password1234",
        "password_eval": "password1234",
        "bulk_email": True,
    }


@pytest.fixture(scope="function")
def user_data_minimal():
    return {
        "email": "user@esherpa.io",
        "password": "password1234",
        "password_eval": "password1234",
    }


@pytest.fixture(scope="function")
def add_user(client, user_auth, user_data):
    return client.post(
        "/api/v1/users",
        headers=user_auth,
        json=user_data,
    )


@pytest.fixture(scope="function")
def add_user_minimal(client, user_auth, user_data_minimal):
    return client.post(
        "/api/v1/users",
        headers=user_auth,
        json=user_data_minimal,
    )
