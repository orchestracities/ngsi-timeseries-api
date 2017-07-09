from translators.crate import CrateTranslator
from translators.influx import InfluxTranslator
from translators.rethink import RethinkTranslator
import os
import pytest

CRATE_HOST = os.environ.get('CRATE_HOST', 'crate')
INFLUX_HOST = os.environ.get('INFLUX_HOST', 'influx')
RETHINK_HOST = os.environ.get('RETHINK_HOST', 'rethink')


@pytest.fixture
def influx_translator():
    trans = InfluxTranslator(INFLUX_HOST)
    trans.setup()

    yield trans

    trans.dispose()


@pytest.fixture()
def crate_translator():
    trans = CrateTranslator(CRATE_HOST)
    trans.setup()

    yield trans

    trans.dispose(testing=True)


@pytest.fixture()
def rethink_translator():
    trans = RethinkTranslator(RETHINK_HOST)
    trans.setup()

    yield trans

    trans.dispose()
