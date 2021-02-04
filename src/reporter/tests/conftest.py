import pytest

from reporter.tests.embedded_server import start_embedded_flask


@pytest.fixture(scope='session', autouse=True)
def embedded_flask():
    start_embedded_flask()
