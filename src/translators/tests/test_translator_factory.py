import os
import pytest
import tempfile

from translators.crate import CrateTranslator
from translators.timescale import PostgresTranslator
from translators.factory import QL_CONFIG_ENV_VAR, translator_for


def write_config() -> str:
    temp = tempfile.TemporaryFile(mode='w+t')
    try:
        temp.writelines('')
        return temp.name
    finally:
        temp.close()


@pytest.fixture(scope='module')
def with_config():
    path = os.path.join(os.path.dirname(__file__), 'ql-config.yml')
    os.environ[QL_CONFIG_ENV_VAR] = path
    pg_port_var = 'POSTGRES_PORT'
    os.environ[pg_port_var] = '54320'
    yield {}
    os.environ[QL_CONFIG_ENV_VAR] = ''
    os.environ[pg_port_var] = ''


def test_tenant1(with_config):
    with translator_for('t1') as t:
        assert isinstance(t, PostgresTranslator)


def test_tenant2(with_config):
    with translator_for('t2') as t:
        assert isinstance(t, CrateTranslator)


def test_tenant3(with_config):
    with translator_for('t3') as t:
        assert isinstance(t, PostgresTranslator)


def test_unknown_tenant(with_config):
    with translator_for('not-in-config') as t:
        assert isinstance(t, CrateTranslator)
