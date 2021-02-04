from translators.crate import CrateTranslator
from translators.timescale import PostgresTranslator
from translators.factory import translator_for
import os

# NOTE. Config file location set by run_tests.sh:
#   QL_CONFIG='src/translators/tests/ql-config.yml'


def test_tenant1():
    with translator_for('t1') as t:
        assert isinstance(t, PostgresTranslator)


def test_tenant2():
    with translator_for('t2') as t:
        assert isinstance(t, CrateTranslator)


def test_tenant3():
    with translator_for('t3') as t:
        assert isinstance(t, PostgresTranslator)


def test_unknown_tenant():
    with translator_for('not-in-config') as t:
        assert isinstance(t, CrateTranslator)


def test_no_tenant():
    with translator_for(None) as t:
        assert isinstance(t, CrateTranslator)


def test_os_env():
    os.environ['QL_DEFAULT_DB'] = 'timescale'
    with translator_for(None) as t:
        assert isinstance(t, PostgresTranslator)
    os.environ['QL_DEFAULT_DB'] = 'crate'
    with translator_for(None) as t:
        assert isinstance(t, CrateTranslator)
    os.environ['QL_DEFAULT_DB'] = ''


def test_fix_404():
    with translator_for(None) as t:
        assert isinstance(t, CrateTranslator)
    os.environ['QL_CONFIG'] = 'src/translators/tests/ql-config-timescale-default.yml'
    with translator_for(None) as t:
        assert isinstance(t, PostgresTranslator)
