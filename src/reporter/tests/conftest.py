import pytest
from fastapi.testclient import TestClient

from main import app
from reporter.tests.embedded_server import start_embedded_flask


@pytest.fixture(scope='session', autouse=True)
def embedded_flask():
    start_embedded_flask()


@pytest.fixture(scope='session', autouse=True)
def client():
    with TestClient(app) as client:
        yield client
