from datetime import datetime
from typing import Iterable, Union
from utils.common import iter_entity_attrs
from utils.jsondict import maybe_value, maybe_string_match
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


def _attribute_key_values(notification: dict, attr_name: str) -> MaybeString:
    return maybe_value(notification, attr_name)


def _meta_attribute(notification: dict, attr_name: str, meta_name: str) \
        -> MaybeString:
    return maybe_value(notification,
                       attr_name, 'metadata', meta_name, 'value')


def _json_ld_meta_attribute(
        notification: dict,
        attr_name: str,
        meta_name: str) -> MaybeString:
    return maybe_value(notification,
                       attr_name, meta_name)


def _iter_metadata(
        notification: dict,
        meta_name: str) -> Iterable[MaybeString]:
    for attr_name in iter_entity_attrs(notification):
        yield _meta_attribute(notification, attr_name, meta_name)


def _iter_json_ld_metadata(
        notification: dict,
        meta_name: str) -> Iterable[MaybeString]:
    for attr_name in iter_entity_attrs(notification):
        yield _json_ld_meta_attribute(notification, attr_name, meta_name)


def time_index_priority_list(
        custom_index: str,
        notification: dict) -> datetime:
    """
    Returns the next possible time_index value using the strategy described in
    the function select_time_index_value.
    """
    # Custom time index attribute
    yield to_datetime(_attribute(notification, custom_index))

    # The most recent custom time index metadata
    yield latest_from_str_rep(_iter_metadata(notification, custom_index))

    # TimeInstant attribute
    yield to_datetime(_attribute(notification, "TimeInstant"))

    # The most recent TimeInstant metadata
    yield latest_from_str_rep(_iter_metadata(notification, "TimeInstant"))

    # timestamp attribute
    yield to_datetime(_attribute(notification, "timestamp"))

    # The most recent timestamp metadata
    yield latest_from_str_rep(_iter_metadata(notification, "timestamp"))

    # The most recent observedAt json-ld metadata
    yield latest_from_str_rep(_iter_json_ld_metadata(notification, "observedAt"))

    # The most recent modifiedAt json-ld metadata
    yield latest_from_str_rep(_iter_json_ld_metadata(notification, "modifiedAt"))

    # observedAt attribute
    yield to_datetime(_attribute_key_values(notification, "observedAt"))

    # modifiedAt attribute
    yield to_datetime(_attribute_key_values(notification, "modifiedAt"))

    # dateModified attribute
    yield to_datetime(_attribute(notification, "dateModified"))

    # The most recent dateModified metadata
    yield latest_from_str_rep(_iter_metadata(notification, "dateModified"))


def select_time_index_value(custom_index: str, notification: dict) -> datetime:
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
    - Custom time index metadata. The most recent custom time index attribute
      value found in any of the attribute metadata sections in the notification
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

    :param custom_index: name of the custom_index (if requested,
    None otherwise)
    :param notification: the notification JSON payload as received from Orion.
    :return: the value to be used as time index.
    """
    current_time = datetime.now()

    for index_candidate in time_index_priority_list(
            custom_index, notification):
        if index_candidate:
            return index_candidate

    # use the current time as a last resort
    return current_time


def select_time_index_value_as_iso(custom_index: str, notification: dict) -> \
        str:
    """
    Same as ``select_time_index_value`` but formats the returned ``datetime``
    as an ISO 8601 string.
    """
    return select_time_index_value(custom_index, notification).isoformat()
