import pytest


@pytest.fixture(scope="session")
def INVALID_ID():
    return 999999


@pytest.fixture(scope="session")
def EMPTY_DICT():
    return {}
