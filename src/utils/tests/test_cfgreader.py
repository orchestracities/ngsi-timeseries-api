import pytest

from utils.cfgreader import *


unset_env_values = [None, '', ' ', '   ', '\t', '\n', '\r\n', '\n\r', ' \t ']

MY_VAR = 'MY_VAR'

unset_env_var = [{MY_VAR: v} for v in unset_env_values] + [{}]


@pytest.mark.parametrize('value, expected', [
    (None, ''), ('', ''),
    (' ', ''), ('\t', ''), ('\n', ''), ('\r\n', ''),
    (' x', 'x'), ('\tx ', 'x'), ('x\n', 'x'), (' x ', 'x')
])
def test_str_var(value, expected):
    var = StrVar('V', '')
    assert var.read(value) == expected


@pytest.mark.parametrize('value', unset_env_values)
def test_str_var_default(value):
    def_val = 'some default value'
    var = StrVar('V', def_val)
    assert var.read(value) == def_val


@pytest.mark.parametrize('value, expected', [
    (' 5', 5), ('\t5 ', 5), ('5\n', 5), (' 5 ', 5),
    (' 5432', 5432), ('\t5432 ', 5432), ('5432\n', 5432), (' 5432 ', 5432)
])
def test_int_var(value, expected):
    var = IntVar('V', None)
    assert var.read(value) == expected


@pytest.mark.parametrize('value', unset_env_values)
def test_int_var_default(value):
    def_val = 12345
    var = IntVar('V', def_val)
    assert var.read(value) == def_val


@pytest.mark.parametrize('value, expected', [
    (' 5', False), ('\t5 ', False), ('5\n', False), (' 5 ', False),
    ('false', False),
    ('t', True), (' t', True), ('\tt ', True), ('t\n', True), (' t ', True),
    ('T', True), (' T', True), ('\tT ', True), ('T\n', True), (' T ', True),
    ('1', True), (' 1', True), ('\t1 ', True), ('1\n', True), (' 1 ', True),
    ('yes', True), (' yes', True), ('\tyes ', True), ('yes\n', True),
    (' yes ', True),
    ('y', True), (' y', True), ('\ty ', True), ('y\n', True), (' y ', True),
    ('Y', True), (' Y', True), ('\tY ', True), ('Y\n', True), (' Y ', True),
    ('true', True), (' true', True), ('\ttrue ', True), ('true\n', True),
    (' true ', True),
    ('True', True), (' tRue', True), ('\ttruE ', True), ('TRUE\n', True),
    (' TrUe ', True)
])
def test_bool_var(value, expected):
    var = BoolVar('V', None)
    assert var.read(value) == expected


@pytest.mark.parametrize('value', unset_env_values)
def test_bool_var_default(value):
    def_val = True
    var = BoolVar('V', def_val)
    assert var.read(value) == def_val


def read_var(store, mask_value):
    logs = {'captured': None}

    def log(msg):
        logs['captured'] = msg

    reader = EnvReader(store, log=log)
    def_val = 'my default value'
    var = StrVar(MY_VAR, def_val, mask_value=mask_value)

    return var, reader.read(var), logs['captured']


@pytest.mark.parametrize('store', unset_env_var)
def test_read_unmasked_default_value(store):
    var, value, log_msg = read_var(store, mask_value=False)

    assert value == var.default_value
    assert f"{var.name} not set" in log_msg
    assert var.default_value in log_msg


@pytest.mark.parametrize('store', unset_env_var)
def test_read_masked_default_value(store):
    var, value, log_msg = read_var(store, mask_value=True)

    assert value == var.default_value
    assert f"{var.name} not set" in log_msg
    assert var.default_value not in log_msg


@pytest.mark.parametrize('store', [
    {MY_VAR: ' x&y '}, {MY_VAR: 'x&y'}, {MY_VAR: 'x&y '}, {MY_VAR: ' x&y'}
])
def test_read_unmasked_value(store):
    var, value, log_msg = read_var(store, mask_value=False)

    assert value == 'x&y'
    assert f"{var.name} set" in log_msg
    assert 'x&y' in log_msg


@pytest.mark.parametrize('store', [
    {MY_VAR: ' x&y '}, {MY_VAR: 'x&y'}, {MY_VAR: 'x&y '}, {MY_VAR: ' x&y'}
])
def test_read_masked_value(store):
    var, value, log_msg = read_var(store, mask_value=True)

    assert value == 'x&y'
    assert f"{var.name} set" in log_msg
    assert 'x&y' not in log_msg


yaml_file = os.path.join(os.path.dirname(__file__), 'test.yml')
yaml_dict = {
    'x': {
        'x1': {'v': 'v1'},
        'x2': {'v': 'v2'}
    },
    'y': 'why'
}


def test_read_yaml_file():
    actual = YamlReader().from_file(yaml_file, {})
    assert actual == yaml_dict


def test_read_yaml_file_specified_by_env_var():
    env_var_name = 'PATH'
    reader = YamlReader({env_var_name: yaml_file})

    actual = reader.from_env_file(env_var_name, {})
    assert actual == yaml_dict


@pytest.mark.parametrize('store', unset_env_var)
def test_read_yaml_file_specified_by_empty_env_var(store):
    reader = YamlReader(store)
    defaults = {'some': 'default'}

    actual = reader.from_env_file(MY_VAR, defaults)
    assert actual == defaults
