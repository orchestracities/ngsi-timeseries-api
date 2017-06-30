import pytest


@pytest.fixture
def app():
    from reporter.reporter import app
    return app
