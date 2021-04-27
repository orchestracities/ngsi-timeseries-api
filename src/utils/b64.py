"""
This module provides utilities to convert strings to Base64 and back.
"""

from base64 import standard_b64encode, standard_b64decode


B64Str = str
"""
A UTF-8 string containing a Base64-encoded string.
"""

UTF8 = 'utf-8'


def to_b64(value: str) -> B64Str:
    """
    Converts a string to its Base64 representation.

    :param value: string to convert, must not be ``None``.
    :return: a string containing the Base64 representation of ``value``.
    """
    value_bytes = value.encode(UTF8)
    b64_bytes = standard_b64encode(value_bytes)
    return b64_bytes.decode(UTF8)


def from_b64(value: B64Str) -> str:
    """
    Converts a Base64 representation of a string back to the original
    string value.

    :param value: the output of ``to_b64(x)``.
    :return: ``x``.
    """
    value_bytes = value.encode(UTF8)
    b64_bytes = standard_b64decode(value_bytes)
    return b64_bytes.decode(UTF8)


B64_LIST_SEPARATOR = ':'
"""
The character used to separate list elements in the Base64 lists produced
by ``to_b64_list``.
"""


def to_b64_list(xs: [str]) -> str:
    """
    Convert each list element to Base64 and join the converted elements
    with a colon. Convert the empty list to an empty string. Take the
    Base64-encoded value of an empty input list element to be ``'""'``.
    Error out if any list element is ``None``.

    :param xs: the input list, must not be ``None``.
    :return: a colon-separated string ``x0:x1:...`` where ``xN`` is the
        Base64-encoded value of ``xs[N]`` or the empty string if ``xs``
        is empty.
    """
    def encode(x: str):
        return '""' if x == '' else to_b64(x)
    encoded_xs = [encode(x) for x in xs]
    return B64_LIST_SEPARATOR.join(encoded_xs)


def from_b64_list(x: str) -> [str]:
    """
    Reverse the ``to_b64_list`` transformation.

    :param x: the output of ``to_b64_list``, never pass in ``None``.
    :return: the input originally passed in to ``to_b64_list``.
    """
    def decode(v: str):
        return '' if v == '""' else from_b64(v)

    if x == '':
        return []
    encoded_xs = x.split(B64_LIST_SEPARATOR)
    return [decode(v) for v in encoded_xs]
