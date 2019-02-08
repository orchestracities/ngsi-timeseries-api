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


def _custom_time_index_attribute(headers: dict, notification: dict) \
        -> MaybeString:
    attr_name = maybe_value(headers, TIME_INDEX_HEADER_NAME)
    if attr_name:
        return maybe_value(notification, attr_name, 'value')
    return None


def _time_instant_attribute(notification: dict) -> MaybeString:
    return maybe_value(notification, 'TimeInstant', 'value')


def _meta_time_instant_attribute(notification: dict, attr_name: str) \
        -> MaybeString:
    return maybe_value(notification,
                       attr_name, 'metadata', 'TimeInstant', 'value')


def _date_modified_attribute(notification: dict) -> MaybeString:
    return maybe_value(notification, 'dateModified', 'value')


def _meta_date_modified_attribute(notification: dict, attr_name: str) \
        -> MaybeString:
    return maybe_value(notification,
                       attr_name, 'metadata', 'dateModified', 'value')


def _iter_time_instant_in_metadata(notification: dict) -> Iterable[MaybeString]:
    for attr_name in iter_entity_attrs(notification):
        yield _meta_time_instant_attribute(notification, attr_name)


def _iter_date_modified_in_metadata(notification: dict) \
        -> Iterable[MaybeString]:
    for attr_name in iter_entity_attrs(notification):
        yield _meta_date_modified_attribute(notification, attr_name)


def select_time_index_value(headers: dict, notification: dict) -> datetime:
    custom_index = to_datetime(
                            _custom_time_index_attribute(headers, notification))
    time_instant = to_datetime(_time_instant_attribute(notification))
    meta_time_instant = latest_from_str_rep(
                                _iter_time_instant_in_metadata(notification))
    date_modified = to_datetime(_date_modified_attribute(notification))
    meta_date_modified = latest_from_str_rep(
                                _iter_date_modified_in_metadata(notification))
    default_value = datetime.now()

    priority_list = [
        custom_index, time_instant, meta_time_instant, date_modified,
        meta_date_modified, default_value
    ]

    return [d for d in priority_list if d][0]
    # Note. Index will never be out of bounds since we added a default value.
