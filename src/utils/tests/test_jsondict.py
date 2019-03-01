import pytest
from utils.jsondict import *


@pytest.mark.parametrize('maybe_dict, key, expected', [
    ({}, '', None), ({}, 'k', None),
    (123, '', 123), (123, 'k', 123),
    ({'h': 1}, '', None), ({'h': 1}, 'k', None),
    ({'k': 1}, '', None), ({'k': 1}, 'k', 1)
])
def test_safe_get_value(maybe_dict, key, expected):
    assert safe_get_value(maybe_dict, key) == expected


@pytest.mark.parametrize('tree, path, expected', [
    ({}, [], []), ({}, [''], [None]), ({}, ['h'], [None]),
    ({}, ['h', 'k'], [None, None]),
    ({'h': 1}, [], []), ({'h': 1}, [''], [None]), ({'h': 1}, ['h'], [1]),
    ({'h': 1}, ['h', 'k'], [1, None]),
    ({'h': {'k': 2}}, [], []), ({'h': {'k': 2}}, [''], [None]),
    ({'h': {'k': 2}}, ['h'], [{'k': 2}]),
    ({'h': {'k': 2}}, ['h', 'k'], [{'k': 2}, 2]),
    ({'h': {'k': 2}}, ['h', 'k', 'j'], [{'k': 2}, 2, None]),
    ({'h': {'k': {'j': 3}}}, ['h', 'k', 'j'],
     [{'k': {'j': 3}}, {'j': 3}, 3])
])
def test_collect_values(tree, path, expected):
    vs = collect_values(tree, *path)
    assert expected == list(vs)


@pytest.mark.parametrize('tree, path, expected', [
    ({}, [], None), ({}, [''], None), ({}, ['h'], None),
    ({}, ['h', 'k'], None),
    ({'h': 1}, [], None), ({'h': 1}, [''], None), ({'h': 1}, ['h'], 1),
    ({'h': 1}, ['h', 'k'], None),
    ({'h': {'k': 2}}, [], None), ({'h': {'k': 2}}, [''], None),
    ({'h': {'k': 2}}, ['h'], {'k': 2}),
    ({'h': {'k': 2}}, ['h', 'k'], 2),
    ({'h': {'k': 2}}, ['h', 'k', 'j'], None),
    ({'h': {'k': {'j': 3}}}, ['h', 'k', 'j'], 3),
    ({'h': {'k': {'j': 3}}}, ['h', 'k', 'j', 'x', 'y'], None)
])
def test_maybe_value(tree, path, expected):
    assert expected == maybe_value(tree, *path)
