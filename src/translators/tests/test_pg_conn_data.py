import pytest

from translators.timescale import PostgresConnectionData


def assert_conn_param(getter, env_var_name, env_var_value,
                      expected_param_value=None):
    conn_data = PostgresConnectionData()
    default_value = getter(conn_data)
    conn_data.read_env(env={env_var_name: env_var_value})

    if expected_param_value:
        assert getter(conn_data) == expected_param_value
    else:
        assert getter(conn_data) == default_value


def get_host(c: PostgresConnectionData): return c.host


def get_port(c: PostgresConnectionData): return c.port


def get_ssl(c: PostgresConnectionData): return c.use_ssl


def get_db_name(c: PostgresConnectionData): return c.db_name


def get_db_user(c: PostgresConnectionData): return c.db_user


def get_db_pass(c: PostgresConnectionData): return c.db_pass


@pytest.mark.parametrize('getter, env_var_name', [
    (get_host, 'POSTGRES_HOST'),
    (get_port, 'POSTGRES_PORT'),
    (get_ssl, 'POSTGRES_USE_SSL'),
    (get_db_name, 'POSTGRES_DB_NAME'),
    (get_db_user, 'POSTGRES_DB_USER'),
    (get_db_pass, 'POSTGRES_DB_PASS')
])
def test_param_default(getter, env_var_name):
    assert_conn_param(getter, env_var_name, '')


@pytest.mark.parametrize('getter, env_var_name, env_value, expected_param', [
    (get_host, 'POSTGRES_HOST', ' my.host ', 'my.host'),
    (get_port, 'POSTGRES_PORT', ' 5432 ', 5432),
    (get_ssl, 'POSTGRES_USE_SSL', ' no ', False),
    (get_ssl, 'POSTGRES_USE_SSL', ' yes ', True),
    (get_db_name, 'POSTGRES_DB_NAME', 'quantumleap\n', 'quantumleap'),
    (get_db_user, 'POSTGRES_DB_USER', '\tquantumleap', 'quantumleap'),
    (get_db_pass, 'POSTGRES_DB_PASS', ' p4ss ', 'p4ss')
])
def test_param(getter, env_var_name, env_value, expected_param):
    assert_conn_param(getter, env_var_name, env_value, expected_param)
