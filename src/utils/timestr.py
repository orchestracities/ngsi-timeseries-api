"""
This module provides utilities to work with string representations of time
points.
"""

from dateutil.parser import parse
from datetime import datetime
from typing import Iterable, Union

MaybeString = Union[str, None]
MaybeDateTime = Union[datetime, None]


def to_datetime(rep: MaybeString) -> MaybeDateTime:
    """
    Convert a string representation of a time point to a ``datetime`` object
    if possible, otherwise return ``None``.

    :param rep: the string representation, typically in ISO 8601 format.
    :return: the converted ``datetime`` or ``None`` if conversion fails.
    """
    if rep and '@value' not in rep:
        try:
            return parse(rep)
        except (ValueError, OverflowError):
            return None
    elif rep and '@value' in rep:
        try:
            return parse(rep['@value'])
        except (ValueError, OverflowError):
            return None
    return None


def latest(ds: Iterable[datetime]) -> MaybeDateTime:
    """
    Pick the most recent time point out of the input lot.

    :param ds: the input time points.
    :return: the most recent time point or ``None`` if the input stream is
        empty.
    """
    xs = sorted(ds)
    if xs:
        return xs[-1]
    return None


def latest_from_str_rep(rs: Iterable[MaybeString]) -> MaybeDateTime:
    """
    Convert the input string representations to ``datetime`` objects and return
    the latest.

    :param rs: input time points in string format, typically ISO 8601.
    :return: the latest time point if at least one string representation
        could be converted or ``None`` otherwise.
    """
    xs = map(to_datetime, rs)
    ys = filter(lambda x: x is not None, xs)
    return latest(ys)
