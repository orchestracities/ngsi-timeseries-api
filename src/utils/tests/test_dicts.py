import pytest
from utils.dicts import *


@pytest.mark.parametrize('ds, key', [
    ({}, None), (None, ''), (None, None)
])
def test_lookup_string_match_with_none_args(ds, key):
    assert lookup_string_match(ds, key) is None


@pytest.mark.parametrize('ds, key', [
    ({}, None), ({}, ''), ({}, 'k')
])
def test_lookup_string_match_with_empty_dict(ds, key):
    assert lookup_string_match(ds, key) is None


@pytest.mark.parametrize('key', [
    'key', 'Key', 'KEy', 'KEY', 'kEy', 'kEY', 'keY'
])
def test_lookup_string_match_with_string_key(key):
    ds = {1: 'a', 'kEy': 'b'}
    assert lookup_string_match(ds, key) == 'b'


def test_lookup_string_match_with_int_key():
    ds = {1: 'a', 'kEy': 'b'}
    assert lookup_string_match(ds, 1) == 'a'
