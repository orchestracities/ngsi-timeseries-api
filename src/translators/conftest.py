from translators.influx import InfluxTranslator
from translators.rethink import RethinkTranslator
import os
import pytest

INFLUX_HOST = os.environ.get('INFLUX_HOST', 'influx')
RETHINK_HOST = os.environ.get('RETHINK_HOST', 'rethink')


@pytest.fixture
def influx_translator():
    with InfluxTranslator(INFLUX_HOST) as trans:
        yield trans


@pytest.fixture()
def rethink_translator():
    with RethinkTranslator(RETHINK_HOST) as trans:
        yield trans
