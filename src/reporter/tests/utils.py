from conftest import QL_URL
from datetime import datetime, timedelta, timezone
import json
import requests
import time
from typing import Callable, Iterable, List, Tuple, Union


def notify_url():
    return "{}/notify".format(QL_URL)


def get_notification(et, ei, attr_value, mod_value):
    return {
        'subscriptionId': '5947d174793fe6f7eb5e3961',
        'data': [
            {
                'id': ei,
                'type': et,
                'temperature': {
                    'type': 'Number',
                    'value': attr_value,
                    'metadata': {
                        'dateModified': {
                            'type': 'DateTime',
                            'value': mod_value
                        }
                    }
                },
                'pressure': {
                    'type': 'Number',
                    'value': 10 * attr_value,
                    'metadata': {
                        'dateModified': {
                            'type': 'DateTime',
                            'value': mod_value
                        }
                    }
                }
            }
        ]
    }


def send_notifications(service, notifications):
    assert isinstance(notifications, list)
    for n in notifications:
        h = {'Content-Type': 'application/json',
             'Fiware-Service': service}
        r = requests.post(notify_url(), data=json.dumps(n), headers=h)
        assert r.ok


def insert_test_data(service, entity_types, n_entities=1, index_size=30,
                     entity_id=None, index_base=None, index_period="day"):
    assert isinstance(entity_types, list)
    index_base = index_base or datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc)

    for et in entity_types:
        for ei in range(n_entities):
            for i in range(index_size):
                if index_period == "year":
                    d = timedelta(days=365 * i)
                elif index_period == "month":
                    d = timedelta(days=31 * i)
                elif index_period == "day":
                    d = timedelta(days=i)
                elif index_period == "hour":
                    d = timedelta(hours=i)
                elif index_period == "minute":
                    d = timedelta(minutes=i)
                elif index_period == "second":
                    d = timedelta(seconds=i)
                else:
                    assert index_period == "milli"
                    d = timedelta(milliseconds=i)
                dt = index_base + d
                dt = dt.isoformat(timespec='milliseconds')

                eid = entity_id or '{}{}'.format(et, ei)
                n = get_notification(et, eid, attr_value=i, mod_value=dt)
                send_notifications(service, [n])

    time.sleep(1)


def delete_entity_type(service, entity_type):
    h = {'Fiware-Service': service}
    url = '{}/types/{}'.format(QL_URL, entity_type)

    r = requests.delete(url, headers=h)
#    assert r.status_code == 204


def delete_test_data(service, entity_types):
    assert isinstance(entity_types, list)

    for et in entity_types:
        delete_entity_type(service, et)


def enum(lo: int, hi: int) -> List[int]:
    return list(range(lo, hi + 1))  # [lo, lo+1, ..., hi]


def temperatures(lo: int, hi: int) -> List[float]:
    return enum(lo, hi)  # insert_test_data generates temps: 0, 1, 2, ...


MaybeInt = Union[int, None]
AttrValues = Tuple[str, List[str], List]
#            (entity_id, time_index, values)


class AttrQueryResultFormatter:

    @staticmethod
    def _attr_values(entity_id: str, time_index: List[str],
                     values: List) -> dict:
        return {
            'entityId': entity_id,
            'index': time_index,
            'values': values
        }

    def __init__(self, entity_type: str, attr_name: str):
        self.entity_type = entity_type
        self.attr_name = attr_name

    def _values_for(self, entities: Iterable[AttrValues]) -> List[dict]:
        return [{
            'entities': [self._attr_values(*e) for e in entities],
            'entityType': self.entity_type
        }]

    def format(self, entities: Iterable[AttrValues], values_only=False) -> dict:
        values = self._values_for(entities)

        if values_only:
            return {
                'values': values
            }
        return {
            'attrName': self.attr_name,
            'types': values
        }


class AttrQueryResultGen:

    def __init__(self, time_index_size: int, entity_type: str, attr_name: str,
                 value_generator: Callable[[int, int], List[float]]):
        self.time_index_size = time_index_size
        self.value_generator = value_generator
        self.formatter = AttrQueryResultFormatter(entity_type, attr_name)

    def entity_type(self) -> str:
        return self.formatter.entity_type

    def attr_name(self) -> str:
        return self.formatter.attr_name

    def time_index(self, truncate_millis=False) -> List[str]:
        if truncate_millis:
            pattern = '1970-01-{:02}T00:00:00+00:00'
        else:
            pattern = '1970-01-{:02}T00:00:00.000+00:00'

        return [pattern.format(i) for i in enum(1, self.time_index_size)]

    def time_index_slice(self, lo: int, hi: int) -> List[str]:
        return self.time_index()[lo: hi + 1]
        # index[lo], index[lo+1], ..., index[hi]

    def values(self, entity_ids: Iterable[str],
               ix_lo: MaybeInt, ix_hi: MaybeInt,
               values_only=False) -> dict:
        if ix_lo is None:  # right-unbounded interval
            ix_lo = 0
        if ix_hi is None:  # left-unbounded interval
            ix_hi = self.time_index_size - 1

        ts = self.time_index_slice(ix_lo, ix_hi)
        vs = self.value_generator(ix_lo, ix_hi)
        es = [(eid, ts, vs) for eid in entity_ids]

        return self.formatter.format(es, values_only)

    def aggregate(self, aggregator: Callable[[Iterable[float]], float],
                  entity_ids: Iterable[str],
                  ix_lo: MaybeInt, ix_hi: MaybeInt) -> dict:
        index = self.time_index(truncate_millis=True)
        # weirdly enough QL truncates millis of returned aggregation interval
        # start and end times.

        if ix_lo is None:  # right-unbounded interval
            ix_lo = 0
            from_date = ''
        else:
            from_date = index[ix_lo]  # let it bomb out if out of range

        if ix_hi is None:  # left-unbounded interval
            ix_hi = self.time_index_size - 1
            to_date = ''
        else:
            to_date = index[ix_hi]  # let it bomb out if out of range

        aggr_value = aggregator(self.value_generator(ix_lo, ix_hi))
        aggr_interval = [from_date, to_date]
        es = [(eid, aggr_interval, [aggr_value]) for eid in entity_ids]

        return self.formatter.format(es)
