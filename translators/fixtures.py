from conftest import CRATE_HOST, CRATE_PORT, clean_crate
from translators.crate import CrateTranslator
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
def crate_translator(clean_crate):
    with CrateTranslator(host=CRATE_HOST, port=CRATE_PORT) as trans:
        yield trans


@pytest.fixture()
def rethink_translator():
    with RethinkTranslator(RETHINK_HOST) as trans:
        yield trans
