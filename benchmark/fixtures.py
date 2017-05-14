from benchmark.crate import CrateTranslator
from benchmark.influx import InfluxTranslator
from benchmark.rethink import RethinkTranslator
import pytest


@pytest.fixture
def influx_translator():
    trans = InfluxTranslator()
    trans.setup()

    yield trans

    trans.dispose()


@pytest.fixture()
def crate_translator():
    trans = CrateTranslator()
    trans.setup()

    yield trans

    trans.dispose()


@pytest.fixture()
def rethink_translator():
    trans = RethinkTranslator()
    trans.setup()

    yield trans

    trans.dispose()
