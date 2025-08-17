import pytest
from web.cache import cache_manager
from web.database import conn
from web.database import model as m

#
# Currency
#


@pytest.fixture(scope="function")
def add_currency_eur(client):
    with conn.begin() as s:
        currency = m.Currency(code="EUR", rate=1, symbol="€")
        s.add(currency)
    cache_manager.update(force=True)
    return currency


@pytest.fixture(scope="function")
def add_currency_gbp(client):
    with conn.begin() as s:
        currency = m.Currency(code="GBP", rate=1, symbol="£")
        s.add(currency)
    cache_manager.update(force=True)
    return currency


#
# Region
#


@pytest.fixture(scope="function")
def add_region_europe(client):
    with conn.begin() as s:
        region = m.Region(name="Europe")
        s.add(region)
    cache_manager.update(force=True)
    return region


#
# Country
#


@pytest.fixture(scope="function")
def add_country_nl(client, add_currency_eur, add_region_europe):
    with conn.begin() as s:
        country = m.Country(
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
        country = m.Country(
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
        language = m.Language(
            code="nl",
            in_sitemap=False,
            name="Dutch",
        )
        s.add(language)
    cache_manager.update(force=True)
    return language


#
# Coupon
#


@pytest.fixture(scope="function")
def add_coupon_10perc(client):
    with conn.begin() as s:
        obj = m.Coupon(code="10PERC", rate=0.1)
        s.add(obj)
    cache_manager.update(force=True)
    return obj
