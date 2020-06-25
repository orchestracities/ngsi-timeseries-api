import pytest
from translators.sql_translator import SQLTranslator


def test_default_query_limit_when_no_env_var_set():
    got = SQLTranslator._get_default_limit()
    assert got == 10000

    got = SQLTranslator._get_default_limit(env={})
    assert got == 10000


@pytest.mark.parametrize('value', ['', ' ', '\n', 'yes', '1 2 3'])
def test_default_query_limit_when_env_var_set_to_non_numeric_value(value):
    env = {
        'DEFAULT_LIMIT': value
    }
    got = SQLTranslator._get_default_limit(env=env)
    assert got == 10000


@pytest.mark.parametrize('value, want', [
    ('1', 1), ('2', 2), ('1234', 1234),
    (' 1 ', 1), ('\t2', 2), ('1234\n', 1234)
])
def test_default_query_limit_when_env_var_set(value, want):
    env = {
        'DEFAULT_LIMIT': value
    }
    got = SQLTranslator._get_default_limit(env=env)
    assert got == want
