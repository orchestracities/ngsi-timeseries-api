import os
import pytest

from translators.timescale import to_str, to_bool, to_int,\
    PostgresConnectionData


@pytest.mark.parametrize('value, expected', [
    (None, ''), ('', ''),
    (' ', ''), ('\t', ''), ('\n', ''), ('\r\n', ''),
    (' x', 'x'), ('\tx ', 'x'), ('x\n', 'x'), (' x ', 'x'),
])
def test_to_str(value, expected):
    assert to_str(value) == expected


@pytest.mark.parametrize('value, expected', [
    (' 5', 5), ('\t5 ', 5), ('5\n', 5), (' 5 ', 5)
])
def test_to_int(value, expected):
    assert to_int(value) == expected


@pytest.mark.parametrize('value, expected', [
    (' 5', False), ('\t5 ', False), ('5\n', False), (' 5 ', False),
    ('false', False), ('\t', False), ('\n', False), (' ', False), ('', False),
    ('t', True), (' t', True), ('\tt ', True), ('t\n', True), (' t ', True),
    ('T', True), (' T', True), ('\tT ', True), ('T\n', True), (' T ', True),
    ('1', True), (' 1', True), ('\t1 ', True), ('1\n', True), (' 1 ', True),
    ('yes', True), (' yes', True), ('\tyes ', True), ('yes\n', True),
    (' yes ', True),
    ('true', True), (' true', True), ('\ttrue ', True), ('true\n', True),
    (' true ', True),
    ('True', True), (' tRue', True), ('\ttruE ', True), ('TRUE\n', True),
    (' TrUe ', True)
])
def test_to_bool(value, expected):
    assert to_bool(value) == expected


def with_env_var(name, value, action):  # TODO how to turn into pytest fixture?
    os.environ[name] = value
    action()
    os.environ[name] = ''


def assert_conn_param(getter, env_var_name, env_var_value,
                      expected_param_value=None):
    def assert_value():
        conn_data = PostgresConnectionData()
        default_value = getter(conn_data)
        conn_data.read_env()

        if expected_param_value:
            assert getter(conn_data) == expected_param_value
        else:
            assert getter(conn_data) == default_value

    with_env_var(env_var_name, env_var_value, assert_value)


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
