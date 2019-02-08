"""
This module provides utilities to work with JSON data represented as
a Python dictionary tree.
"""

from typing import Iterable


def safe_get_value(maybe_dict, key: str):
    """
    Get the value for `key` if `maybe_dict` is a `dict` and has that
    key. If `key` isn't there return `None`. Otherwise, `maybe_dict`
    isn't a `dict`, so return `maybe_dict` as is.
    """
    if isinstance(maybe_dict, dict):
        return maybe_dict.get(key, None)
    return maybe_dict


def collect_values(tree: dict, *path_components: str) -> Iterable:
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
    :return: an iterable containing the sequence ``v0, v1, ..``.
    """
    for key in path_components:
        v = tree.get(key, None)
        tree = v if isinstance(v, dict) else {}
        yield v


def maybe_value(tree: dict, *path_components: str):
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
    :return: the value, if any, corresponding to the last key in the path.
    """
    if path_components:
        vs = collect_values(tree, *path_components)
        return list(vs)[len(path_components) - 1]
    return None
