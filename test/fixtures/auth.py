import pytest


@pytest.fixture(scope="session")
def guest_auth():
    return {"Authorization": "Bearer guest"}


@pytest.fixture(scope="session")
def user_auth():
    return {"Authorization": "Bearer user"}


@pytest.fixture(scope="session")
def admin_auth():
    return {"Authorization": "Bearer admin"}
