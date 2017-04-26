import pytest
from influxdb import InfluxDBClient
import random
import string


# These defaults are to be used with the influx run by the benchmark/docker-compose.yml file.
INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
DB_NAME = "ngsi-tsdb"


@pytest.fixture
def db_client():
    client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, 'root', 'root')
    client.create_database(DB_NAME)
    yield client
    client.drop_database(DB_NAME)


# for testing only
attr_to_type = {
    "attr_str": "string",
    "attr_float": "number",
    "attr_bool": "boolean",
}

def iter_random_entities(num_types=10, num_ids_per_type=10, use_string=True, use_number=True, use_boolean=True,
                         use_geo=False):
    """
    :param num_types:
    :param num_ids_per_type:
    :param string:
    :param number:
    :param boolean:
    :param geo:
    :return: Iter NGSI entities in JSON representation format.
    """
    for nt in range(num_types):
        for ni in range(num_ids_per_type):
            entity = {
                "type": "{}".format(nt),
                "id": "{}-{}".format(nt, ni),
            }
            if use_string:
                entity["attr_str"] = {
                    "value": ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
                    "type": attr_to_type["attr_str"],
                }
            if use_number:
                entity["attr_float"] = {
                    "value": random.uniform(0,1),
                    "type": attr_to_type["attr_float"],
                }
            if use_boolean:
                entity["attr_bool"] = {
                    "value": bool(random.choice((0, 1))),
                    "type": attr_to_type["attr_bool"],
                }
            if use_geo:
                raise NotImplementedError
            yield entity


def iter_influx_points(entities):
    """
    :param entities: iterable of NGSI Entity dicts
    :return: iterator on Influxdb Json representation of measurement points.
    """

    for ent in entities:
        for attr in ent:
            if attr in ("id", "type"):
                continue
            p = {
                "measurement": attr,
                "tags": {
                    "entity_type": ent["type"],
                    "entity_id": ent["id"]
                },
                "fields": {
                    "value": ent[attr]["value"]
                }
            }
            yield p


def entity_pk(entity):
    """
    :param entity: NGSI Entity JSON representation
    :return: unicode NGSI Entity "unique" identifier.
    """
    if 'type' not in entity and 'id' not in entity:
        # Allowance for tsdb back-and-forth
        t, i = entity['entity_type'], entity['entity_id']
    else:
        t, i = entity['type'], entity['id']
    return "t:{}i:{}".format(t, i)


def iter_entities(resultsets):
    """
    :param resultsets: list(ResultSet)
    :return: list(dict)
    """
    entities = {}
    for rs in resultsets:
        for k, seriepoints in rs.items():
            attr = k[0]
            for p in seriepoints:  # This level of for evidences why this is just for small testing purposes
                e = {"type": p['entity_type'], "id": p['entity_id']}
                e = entities.setdefault(entity_pk(e), e)
                e[attr] = {"type": attr_to_type[attr], "value": p['value']}
    return entities.values()


def test_insert(db_client):
    points = list(iter_influx_points(list(iter_random_entities(2, 2))))
    result = db_client.write_points(points, database=DB_NAME)
    assert result


def test_list_entities(db_client):
    """
    When querying InfluxDB, remember that there must be at least one field in the select to get results, using only
    time/tags will not return data.
    """
    # Write points
    entities = list(iter_random_entities(num_types=10, num_ids_per_type=10, use_string=True, use_number=True,
                                         use_boolean=True, use_geo=False))
    points = list(iter_influx_points(entities))
    result = db_client.write_points(points, database=DB_NAME)
    assert result

    # Queries in Influx are done first by measurement, then of course you can filter.
    # More info: https://docs.influxdata.com/influxdb/v1.2/query_language/data_exploration/

    # For testing purposes, let's get all entities back (querying accross multiple measurements). Of course, in practice
    # this is not the right approach.
    rs = db_client.query("SHOW MEASUREMENTS", database=DB_NAME)
    measurements = [m[0] for m in rs.raw['series'][0]['values']]

    # Be careful when selecting multiple measurements in the same query. If fields names are the same, influxdb will not
    # automatically rename those columns, it will preserve only one.
    query = ""
    for m in measurements:
        query += "select * from {};".format(m)

    # TODO: Test with DataFrameClient
    result = db_client.query(query, database=DB_NAME)
    assert len(result) == 3
    loaded_entities = list(iter_entities(result))

    assert sorted(loaded_entities, key=entity_pk) == sorted(entities, key=entity_pk)
