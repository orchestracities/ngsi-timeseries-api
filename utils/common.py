from datetime import datetime
import pytest
import random
import string


TIME_INDEX_NAME = 'time_index'

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
    assert entity.keys() == other.keys()
    for ek, ev in entity.items():
        if isinstance(ev, dict):
            assert_ngsi_entity_equals(ev, other[ek])
        else:
            if isinstance(ev, float):
                assert ev == pytest.approx(other[ek])
            else:
                if ek == 'time_index':
                    d0 = datetime.strptime(ev, "%Y-%m-%dT%H:%M:%S.%f")
                    d1 = datetime.strptime(other[ek], "%Y-%m-%dT%H:%M:%S.%f")
                    assert d0 == d1
                else:
                    if ev != other[ek]:
                        print('Debug!')
                    assert ev == other[ek]


def entity_pk(entity):
    """
    :param entity: NGSI JSON Entity Representation
    :return: unicode NGSI Entity "unique" identifier.
    """
    if 'type' not in entity and 'id' not in entity:
        # Allowance for tsdb back-and-forth.
        # To avoid column name id in databases, we prefix it with entity_. Same for type, for consistence.
        t, i = entity['entity_type'], entity['entity_id']
    else:
        t, i = entity['type'], entity['id']
    return "t:{}i:{}".format(t, i)


def pick_random_entity_id(num_types, num_ids_per_type):
    """
    :param num_types:
    :param num_ids_per_type:
    :return:
    """
    return "{}-{}".format(int(random.uniform(0, num_types)), int(random.uniform(0, num_ids_per_type)))


def create_random_entities(num_types, num_ids_per_type, num_updates, use_time=False, use_geo=False):
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
    def add_attr(ent, attr_name, attr_value):
        ent[attr_name] = {
            "value": attr_value,
            "type": ATTR_TO_TYPE[attr_name]
        }

    # TODO: Rewrite with np and pandas
    entities = []
    for u in range(num_updates):
        for nt in range(num_types):
            for ni in range(num_ids_per_type):
                entity = {
                    "type": "{}".format(nt),
                    "id": "{}-{}".format(nt, ni),
                    # This column is the one added by reporter with notification timestamp
                    # zeroing last 3 digits of microseconds to avoid annoying diffs in testing
                    TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
                }
                # This is to guarantee significant differences among entities for the TIME_INDEX_NAME attribute.
                import time; time.sleep(0.001)

                add_attr(entity, "attr_str", ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),)
                add_attr(entity, "attr_float", random.uniform(0, 1))
                add_attr(entity, "attr_bool", bool(random.choice((0, 1))))

                if use_time:
                    # dt = datetime.now()
                    dt = datetime(1970, round(random.uniform(1, 12)), round(random.uniform(1, 28)), 0, 0, 0, 0)
                    add_attr(entity, "attr_time", dt.isoformat())

                if use_geo:
                    long, lat = random.uniform(-180, 180), random.uniform(-90, 90)
                    point = {"type": "Point", "coordinates": [long, lat]}
                    add_attr(entity, "attr_geo", point)

                entities.append(entity)
    return entities


def iter_entity_attrs(entity):
    for attr in entity:
        if attr not in ['type', 'id']:
            yield attr


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
