"""
This module provides utilities to work with JSON data represented as
a Python dictionary tree.
"""

from typing import Any, Hashable, Iterable, Optional


def safe_get_value(maybe_dict, key: Hashable) -> Optional[Any]:
    """
    Get the value for `key` if `maybe_dict` is a `dict` and has that
    key. If `key` isn't there return `None`. Otherwise, `maybe_dict`
    isn't a `dict`, so return `maybe_dict` as is.
    """
    if isinstance(maybe_dict, dict):
        return maybe_dict.get(key, None)
    return maybe_dict


def lookup_string_match(ds: dict, key: Hashable) -> Optional[Any]:
    """
    Return the first value whose key matches the input key.
    To this function, a matching dictionary key ``k`` is one for which
    ``m(k) = m(key)`` where ``m`` is the function that converts a value
    to a string and then lowercases that string.
    Also, to clarify further, "first" refers to the first match found
    iterating the dictionary keys.

    Examples:

        >>> ds = {'kEy1': 'v1', 2: 'v2', 'key1': 'v3'}

        >>> lookup_string_match(ds, 'key1')
        'v1'

        >>> lookup_string_match(ds, 'Key1')
        'v1'

        >>> lookup_string_match(ds, '2')
        'v2'

        >>> lookup_string_match(ds, 2)
        'v2'

    :param ds: the data.
    :param key: the key for which to find a match.
    :return: the dictionary value of a matched key if one is found, ``None``
        otherwise. Also return ``None`` when either or both input params are
        ``None``.
    """
    if isinstance(ds, dict) and key is not None:
        key_to_match = str(key).lower()
        for k in ds.keys():
            if str(k).lower() == key_to_match:
                return ds[k]
    return None


def collect_values(tree: dict, *path_components: Hashable,
                   lookup=safe_get_value) -> Iterable:
    """
    Collect values ``[v0, v1, ..]`` corresponding to key path ``[k1, k2, ..]``
    on the input dictionary tree. The key sequence may match an actual key path
    or match it up to a point or not match any path at all. If a key ``k[n]``
    in the input sequence isn't in the tree, we set the corresponding value
    ``v[n]`` to ``None``. Since ``k[n+1], k[n+2], ..`` won't be in the
    tree either, ``v[n+1], k[n+2], ..`` will all be ``None`` too.

    Examples:

        >>> tree = {'h': {'k': {'j': 3}}}

        >>> list(collect_values(tree, 'x'))
        [None]

        >>> list(collect_values(tree, 'h', 'k'))
        [{'k': {'j': 3}}, {'j': 3}]

        >>> list(collect_values(tree, 'h', 'k', 'j', 'x', 'y'))
        [{'k': {'j': 3}}, {'j': 3}, 3, None, None]

    :param tree: a tree of dictionaries: inner nodes are dictionaries while any
        non-dictionary value is considered a leaf.
    :param path_components: the key path ``[k1, k2, ..]``.
    :param lookup: optional function (dict, Hashable) -> value. Used internally
        to lookup the next value from the current dictionary and path component
        in the iteration.
    :return: an iterable containing the sequence ``v0, v1, ..``.
    """
    for key in path_components:
        v = lookup(tree, key)
        tree = v if isinstance(v, dict) else {}
        yield v


def maybe_value(tree: dict, *path_components: Hashable, lookup=safe_get_value):
    """
    Get the value corresponding to last key in the key path ``[k1, k2, ..]``
    on the input dictionary tree. The key sequence may match an actual key path
    or match it up to a point or not match any path at all. If a key ``k[n]``
    in the input sequence isn't in the tree, we return ``None``.

    Examples:

        >>> tree = {'h': {'k': {'j': 3}}}

        >>> maybe_value(tree, 'x') is None
        True

        >>> maybe_value(tree, 'h', 'k')
        {'j': 3}

        >>> maybe_value(tree, 'h', 'k', 'j')
        3

        >>> maybe_value(tree, 'h', 'k', 'j', 'x', 'y') is None
        True

    :param tree: a tree of dictionaries: inner nodes are dictionaries while any
        non-dictionary value is considered a leaf.
    :param path_components: the key path ``[k1, k2, ..]``.
    :param lookup: optional function (dict, Hashable) -> value. Used internally
        to lookup the next value from the current dictionary and path component
        in the iteration.
    :return: the value, if any, corresponding to the last key in the path.
    """
    if isinstance(tree, dict) and path_components:
        vs = collect_values(tree, *path_components, lookup=lookup)
        return list(vs)[len(path_components) - 1]
    return None


def maybe_string_match(ds: dict, *path_components: Hashable) -> Optional[Any]:
    """
    Get the value corresponding to last key in the key path ``[k1, k2, ..]``
    on the input dictionary tree. The key sequence may match an actual key path
    or match it up to a point or not match any path at all. If a key ``k[n]``
    in the input sequence isn't in the tree, we return ``None``.

    To this function, a matching dictionary key ``k`` is one for which
    ``m(k) = m(key)`` where ``m`` is the function that converts a value
    to a string and then lowercases that string.
    Also, to clarify further, "first" refers to the first match found
    iterating the dictionary keys.

    Examples:

        >>> ds = {'kEy1': 'v1', 2: {3: 'v2'}, 'key1': 'v3'}

        >>> maybe_string_match(ds, 'key1')
        'v1'

        >>> maybe_string_match(ds, 'Key1')
        'v1'

        >>> maybe_string_match(ds, '2')
        {3: 'v2'}

        >>> maybe_string_match(ds, 2)
        {3: 'v2'}

        >>> maybe_string_match(ds, 2, 3)
        'v2'

    :param ds: the data.
    :param path_components: the key path ``[k1, k2, ..]``.
    :return: the dictionary value of a matched key if one is found, ``None``
        otherwise. Also return ``None`` when either or both input params are
        ``None``.
    """
    return maybe_value(ds, *path_components, lookup=lookup_string_match)
