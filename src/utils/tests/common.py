from datetime import datetime, timezone
import pytest
import random
import string
import dateutil.parser
from utils.common import TIME_INDEX_NAME, entity_pk, iter_entity_attrs

# For testing only, Attr name to NGSI type (are these NGSI types?)
# TODO: Stop using this in Influx and Rethink translators
ATTR_TO_TYPE = {
    "attr_str": "Text",
    "attr_float": "Number",
    "attr_bool": "Boolean",
    "attr_time": "DateTime",
    "attr_geo": "geo:json",
}


def assert_ngsi_entity_equals(entity, other):
    """
    :param dict entity: Dict representing an NGSI entity in JSON Entity Representation.
    :param dict other: Dict representing an NGSI entity in JSON Entity Representation.
    :return:
        Asserts that two NGSI entities are equal. All types are asserted for exact equality, but for float and datetime,
        which are compared using pytest.approx with the given rel and abs params.
    """
    # NGSI Array Attribute? (i.e, python list)
    if isinstance(entity, list) or isinstance(other, list):
        assert isinstance(entity, list) and isinstance(other, list)
        assert entity == other
        return

    # Else, the rest can be treated as a dict
    assert entity.keys() == other.keys(), entity.keys() ^ other.keys()
    for ek, ev in entity.items():
        if isinstance(ev, dict):
            assert_ngsi_entity_equals(ev, other[ek])
        else:
            if isinstance(ev, float):
                assert ev == pytest.approx(other[ek])
            else:
                if ek == 'time_index':
                    assert_equal_time_index_arrays([ev], [other[ek]])
                else:
                    assert ev == other[ek], "{} != {}".format(ev, other[ek])


def pick_random_entity_id(num_types, num_ids_per_type):
    """
    :param num_types:
    :param num_ids_per_type:
    :return:
    """
    return "{}-{}".format(int(random.uniform(0, num_types)),
                          int(random.uniform(0, num_ids_per_type)))


def add_attr(ent, attr_name, attr_value):
    ent[attr_name] = {
        "value": attr_value,
        "type": ATTR_TO_TYPE[attr_name]
    }


def create_random_entities(num_types=1,
                           num_ids_per_type=1,
                           num_updates=1,
                           use_time=False,
                           use_geo=False):
    """
    :param num_types:
    :param num_ids_per_type:
    :param num_updates:
    :param use_string:
    :param use_number:
    :param use_boolean:
    :param use_time:
    :param use_geo:
    :return: Iter NGSI entities in JSON Entity Representation format.
    """

    # TODO: Rewrite with np and pandas
    entities = []
    for u in range(num_updates):
        for nt in range(num_types):
            for ni in range(num_ids_per_type):
                t = datetime.now(timezone.utc).isoformat(
                    timespec='milliseconds')
                entity = {
                    "type": "{}".format(nt),
                    "id": "{}-{}".format(nt, ni),
                    TIME_INDEX_NAME: t,
                }
                # Guarantee significant differences for TIME_INDEX_NAME.
                import time
                time.sleep(0.001)

                a = random.choices(
                    string.ascii_uppercase + string.digits, k=10)
                add_attr(entity, "attr_str", ''.join(a))
                a = float(format(random.uniform(0, 1), '.6f'))
                add_attr(entity, "attr_float", a)
                a = bool(random.choice((0, 1)))
                add_attr(entity, "attr_bool", a)

                if use_time:
                    month = round(random.uniform(1, 12))
                    day = round(random.uniform(1, 28))
                    dt = datetime(1970, month, day, 0, 0, 0, 0, timezone.utc)
                    v_iso = dt.isoformat(timespec='milliseconds')
                    add_attr(entity, "attr_time", v_iso)

                if use_geo:
                    # precision of postgis does not allow more than 16 decimals
                    long = round(random.uniform(-180, 180), 10)
                    lat = round(random.uniform(-90, 90), 10)
                    point = {"type": "Point", "coordinates": [long, lat]}
                    add_attr(entity, "attr_geo", point)

                entities.append(entity)
    return entities


def create_simple_subscription(notify_url):
    subscription = {
        "description": "Test subscription",
        "subject": {
            "entities": [
                {
                    "id": "Room1",
                    "type": "Room"
                }
            ],
            "condition": {
                "attrs": [
                    "pressure",
                    "temperature"
                ]
            }
        },
        "notification": {
            "http": {
                "url": notify_url
            },
            "attrs": [
                "pressure",
                "temperature"
            ]
        },
    }
    return subscription


def create_simple_subscription_v1(notify_url):
    subscription = {
        "entities": [
            {
                "type": "Room",
                "id": "Room1"
            }
        ],
        "attributes": [
            "temperature",
        ],
        "reference": notify_url,
        "notifyConditions": [
            {
                "type": "ONCHANGE",
                "condValues": [
                    "temperature",
                ]
            }
        ],
    }
    return subscription


def assert_equal_time_index_arrays(index1, index2):
    """
    check both time_index are almost equal within QL's time tolerance.
    """
    for d0, d1 in zip(index1, index2):
        d0 = dateutil.parser.isoparse(d0)
        d1 = dateutil.parser.isoparse(d1)
        assert abs(d0 - d1).microseconds < 1000


def check_notifications_record(notifications, records):
    """
    Check that the given NGSI notifications like those sent by Orion
    (Translator Input) are correctly transformed to a set of records
    (Translator Output).
    """
    from translators.sql_translator import NGSI_DATETIME, NGSI_ISO8601
    assert len(notifications) > 0
    assert len(records) == 1

    record = records[0]
    expected_type = record['type']
    expected_id = record['id']

    # all notifications and records should have same type and id
    assert all(map(lambda x: x['type'] == expected_type, notifications))
    assert all(map(lambda x: x['id'] == expected_id, notifications))

    index = [n[TIME_INDEX_NAME] for n in notifications]
    assert_equal_time_index_arrays(index, record['index'])

    for a in iter_entity_attrs(record):
        if a == 'index':
            continue

        r_values = record[a]['values']
        # collect values for the attribute a from the entities in the notification
        # if an entity does not have a value for the attribute use None
        n_values = [e[a]['value'] if a in e else None for e in notifications]

        if any(isinstance(x, float) for x in n_values):
            assert pytest.approx(r_values, n_values)
        else:
            if record[a].get('type', None) in (NGSI_DATETIME, NGSI_ISO8601):
                assert_equal_time_index_arrays(r_values, n_values)
            else:
                assert r_values == n_values, "{} != {}".format(r_values,
                                                               n_values)
