"""
This module provides utilities to work with dictionaries.
"""


def lookup_string_match(ds: dict, key):
    """
    Return the first value whose key matches the input key.
    To this function, a matching dictionary key `k` is one
    for which `m(k) = m(key)` where `m` is the function that
    converts a value to a string and then lowercases that
    string.
    Also, to clarify further, "first" refers to the first
    match found iterating the dictionary keys.

    :param ds: the data.
    :param key: the key for which to find a match.
    :return: the dictionary value of a matched key if one is
        found, `None` otherwise. Also return `None` when either
        or both input params are `None`.
    """
    if ds is not None and key is not None:
        key_to_match = str(key).lower()
        for k in ds.keys():
            if str(k).lower() == key_to_match:
                return ds[k]
    return None
