import pytest


@pytest.fixture(scope="session")
def INVALID_ID():
    return 999999
