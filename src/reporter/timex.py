from datetime import datetime
from typing import Iterable, Union

from utils.common import iter_entity_attrs
from utils.jsondict import maybe_value
from utils.timestr import latest_from_str_rep, to_datetime

TIME_INDEX_HEADER_NAME = 'Fiware-TimeIndex-Attribute'

MaybeString = Union[str, None]


def _first_not_none(xs: Iterable):
    ys = [x for x in xs if x is not None]
    return ys[0]
# NB this function is always called with a sequence containing at least one
# value != None.


def _attribute(notification: dict, attr_name: str) -> MaybeString:
    return maybe_value(notification, attr_name, 'value')


def _meta_attribute(notification: dict, attr_name: str, meta_name: str) \
        -> MaybeString:
    return maybe_value(notification,
                       attr_name, 'metadata', meta_name, 'value')


def _iter_metadata(notification: dict, meta_name: str) -> Iterable[MaybeString]:
    for attr_name in iter_entity_attrs(notification):
        yield _meta_attribute(notification, attr_name, meta_name)


def select_time_index_value(headers: dict, notification: dict) -> datetime:
    """
    Determine which attribute or metadata value to use as a time index for the
    entity being notified.
    The returned value will be the first value found in the below list that can
    be converted to a ``datetime``. Items are considered from top to bottom,
    so that if multiple values are present and they can all be converted to
    ``datetime``, the topmost value is chosen.

    - Custom time index. The value of the ``TIME_INDEX_HEADER_NAME``. Note
      that for a notification to contain such header, the corresponding
      subscription has to be created with an ``httpCustom`` block as detailed
      in the *Subscriptions* and *Custom Notifications* sections of the NGSI
      spec.
    - Custom time inde metadata. The most recent custom time index attribute value
      found in any of the attribute metadata sections in the notification.
    - ``TimeInstant`` attribute.
    - ``TimeInstant`` metadata. The most recent ``TimeInstant`` attribute value
      found in any of the attribute metadata sections in the notification.
    - ``timestamp`` attribute.
    - ``timestamp`` metadata. The most recent ``timestamp`` attribute value
      found in any of the attribute metadata sections in the notification.
    - ``dateModified`` attribute.
    - ``dateModified`` metadata. The most recent ``dateModified`` attribute
      value found in any of the attribute metadata sections in the notification.
    - Current time. This is the default value we use if any of the above isn't
      present or none of the values found can actually be converted to a
      ``datetime``.

    :param headers: the HTTP headers as received from Orion.
    :param notification: the notification JSON payload as received from Orion.
    :return: the value to be used as time index.
    """
    considered_attributes = [
        maybe_value(headers, TIME_INDEX_HEADER_NAME),
        "TimeInstant",
        "timestamp",
        "dateModified"
    ]

    for attr_name in considered_attributes:
        if not attr_name:
            continue

        attr_value = to_datetime(_attribute(notification, attr_name))
        if attr_value:
            return attr_value

        meta_value = latest_from_str_rep(
            _iter_metadata(notification, attr_name))
        if meta_value:
            return meta_value

    return datetime.now()


def select_time_index_value_as_iso(headers: dict, notification: dict) -> str:
    """
    Same as ``select_time_index_value`` but formats the returned ``datetime``
    as an ISO 8601 string.
    """
    return select_time_index_value(headers, notification).isoformat()
