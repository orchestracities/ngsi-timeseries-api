from benchmark.base_translator import BaseTranslator
from datetime import datetime
import pytest
import random
import string


# For testing only, Attr name to NGSI type (are these NGSI types?)
# TODO: Change this to proper attr type mapping

ATTR_TO_TYPE = {
    "attr_str": "Text",
    "attr_float": "Number",
    "attr_bool": "Boolean",
    "attr_time": "DateTime",
    "attr_geo": "json:geo",
}


def assert_ngsi_entity_equals(entity, other):
    """
    :param dict entity: Dict representing an NGSI entity in JSON Entity Representation.
    :param dict other: Dict representing an NGSI entity in JSON Entity Representation.
    :return:
        Asserts that two NGSI entities are equal. All types are asserted for exact equality, but for float and datetime,
        which are compared using pytest.approx with the given rel and abs params.

    NOTE: Metadata not yet supported?
    """
    assert entity.keys() == other.keys()
    for ek, ev in entity.items():
        if isinstance(ev, dict):
            assert_ngsi_entity_equals(ev, other[ek])
        else:
            if isinstance(ev, float):
                assert ev == pytest.approx(other[ek])
            else:
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
                    BaseTranslator.TIME_INDEX_NAME: datetime.now().isoformat(),
                }

                add_attr(entity, "attr_str", ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),)
                add_attr(entity, "attr_float", random.uniform(0, 1))
                add_attr(entity, "attr_bool", bool(random.choice((0, 1))))

                if use_time:
                    dt = datetime(1970, round(random.uniform(1, 12)), round(random.uniform(1, 28)), 0, 0, 0, 0)
                    # chopping last 3 digits of microseconds to avoid annoying diffs in testing
                    add_attr(entity, "attr_time", dt.isoformat()[:-3])

                if use_geo:
                    long, lat = random.uniform(-180, 180), random.uniform(-90, 90)
                    point = {"type": "Point", "coordinates": [long, lat]}
                    add_attr(entity, "attr_geo", point)

                entities.append(entity)
    return entities
