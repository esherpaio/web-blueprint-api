import contextlib

import pytest
from flask import Flask
from sqlalchemy import text
from web.cache import cache_manager
from web.database.client import engine
from web.database.model import Base
from web.logger import log
from web.setup.server import Server

import test.config as config
from web_bp_api import api_bp
from web_bp_webhook import webhook_bp

from .tasks import UserSeedSyncer

pytest_plugins = [
    "test.fixtures.auth",
    "test.fixtures.models",
    "test.fixtures.utils",
]


@pytest.fixture(scope="function", autouse=True)
def drop_tables():
    log.debug("Dropping all tables")
    meta = Base.metadata
    with contextlib.closing(engine.connect()) as conn:
        s = conn.begin()
        conn.execute(text("SET session_replication_role = 'replica'"))
        for table in reversed(meta.sorted_tables):
            conn.execute(
                text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE')
            )
        conn.execute(text("SET session_replication_role = 'origin'"))
        s.commit()
    engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def client(drop_tables):
    app = Flask(__name__)
    web = Server()
    web.setup_database(False, [UserSeedSyncer])
    web.setup_cache()
    web.setup_flask(app, [api_bp, webhook_bp])
    web.setup_jinja(app)
    app.testing = True
    cache_manager.pause()
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def clear_cookies(client):
    log.debug("Clearing cookies")
    if client._cookies is not None:
        client._cookies.clear()


@pytest.fixture
def patch_config(monkeypatch):
    def _patch(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setattr(config, key, value)

    return _patch
