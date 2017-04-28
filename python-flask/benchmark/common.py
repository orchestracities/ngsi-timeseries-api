import random
import string


# for testing only, Attr name to NGSI type (are these NGSI types?)
attr_to_type = {
    "attr_str": "Text",
    "attr_float": "Number",
    "attr_bool": "Boolean",
    "attr_time": "DateTime",
    "attr_geo": "json:geo",
}


def entity_pk(entity):
    """
    :param entity: NGSI Entity JSON representation
    :return: unicode NGSI Entity "unique" identifier.
    """
    if 'type' not in entity and 'id' not in entity:
        # Allowance for tsdb back-and-forth.
        # To avoid column name id in databases, we prefix it with entity_. Same for type, for consistence.
        t, i = entity['entity_type'], entity['entity_id']
    else:
        t, i = entity['type'], entity['id']
    return "t:{}i:{}".format(t, i)


def iter_random_entities(num_types=10, num_ids_per_type=10, use_string=True, use_number=True, use_boolean=True,
                         use_time=False, use_geo=False):
    """
    :param num_types:
    :param num_ids_per_type:
    :param use_string:
    :param use_number:
    :param use_boolean:
    :param use_time:
    :param use_geo:
    :return: Iter NGSI entities in JSON representation format.
    """
    for nt in range(num_types):
        for ni in range(num_ids_per_type):
            entity = {
                "type": "{}".format(nt),
                "id": "{}-{}".format(nt, ni),
            }

            def add_attr(attr_name, attr_value):
                entity[attr_name] = {
                    "value": attr_value,
                    "type": attr_to_type[attr_name]
                }

            if use_string:
                add_attr("attr_str", ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),)

            if use_number:
                add_attr("attr_float", random.uniform(0,1))

            if use_boolean:
                add_attr("attr_bool", bool(random.choice((0, 1))))

            if use_time:
                from datetime import datetime
                add_attr("attr_time", datetime.now().isoformat())

            if use_geo:
                long, lat = random.uniform(-180, 180), random.uniform(-90, 90)
                point = {"type": "Point", "coordinates": [long, lat]}
                add_attr("attr_geo", point)

            yield entity
