import pytest
from influxdb import InfluxDBClient
from benchmark.common import *


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


def iter_influx_points(entities):
    """
    :param entities: iterable of dicts (NGSI JSON Entity Representation)
    :return: iterator on Influxdb JSON representation of measurement points. I.e, NGSI to InfluxDB.
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


def iter_entities(resultsets):
    """
    :param resultsets: list(ResultSet)
    :return: list(dict). I.e, InfluxDB results to NGSI entities (in JSON Entity Representation).
    """
    entities = {}
    for rs in resultsets:
        for k, seriepoints in rs.items():
            attr = k[0]
            for p in seriepoints:  # This level of for evidences why this is just for small testing purposes
                e = {"type": p['entity_type'], "id": p['entity_id']}
                e = entities.setdefault(entity_pk(e), e)
                e[attr] = {"type": ATTR_TO_TYPE[attr], "value": p['value']}
    return entities.values()


def test_insert(db_client):
    """
    https://docs.influxdata.com/influxdb/v1.2/guides/writing_data/
    """
    points = list(iter_influx_points(list(iter_random_entities())))
    result = db_client.write_points(points, database=DB_NAME)
    assert result


def query_all(db_client, db_name, where_clause=""):
    """
    Helper to query all entity data from InfluxDB, "gathering" data from all measurements.
    """
    rs = db_client.query("SHOW MEASUREMENTS", database=db_name)
    measurements = [m[0] for m in rs.raw['series'][0]['values']]

    # Be careful when selecting multiple measurements in the same query. If fields names are the same, influxdb will not
    # automatically rename those columns, it will preserve only one.
    query = ""
    for m in measurements:
        query += "select * from {} {};".format(m, where_clause)

    # TODO: Test with DataFrameClient?
    result = db_client.query(query, database=db_name)
    return result


def test_list_entities(db_client):
    """
    When querying InfluxDB, remember that there must be at least one field in the select to get results, using only
    time/tags will not return data.

    Queries in Influx are done first by measurement, then of course you can filter.

    More info: https://docs.influxdata.com/influxdb/v1.2/query_language/data_exploration/
    """
    entities = list(iter_random_entities())
    points = list(iter_influx_points(entities))
    result = db_client.write_points(points, database=DB_NAME)
    assert result

    # For testing purposes, let's get all entities back (querying accross multiple measurements). Of course, in practice
    # this is not the right approach.
    result = query_all(db_client, DB_NAME)
    assert len(result) == 3

    loaded_entities = list(iter_entities(result))
    assert sorted(loaded_entities, key=entity_pk) == sorted(entities, key=entity_pk)


def update_entities(db_client, num_updates=10, **kwargs):
    for up in range(num_updates):
        points = list(iter_influx_points(iter_random_entities(**kwargs)))
        result = db_client.write_points(points, database=DB_NAME)
        assert result


def test_updates(db_client):
    num_types = 2
    num_ids_per_type = 2
    num_updates = 10

    update_entities(db_client, num_updates, num_types=num_types, num_ids_per_type=num_ids_per_type)

    result = query_all(db_client, DB_NAME)
    assert len(result) == 3, "3 measurements for now"
    for r in result:
        points = list(r.get_points())
        assert len(points) == num_types * num_ids_per_type * num_updates


def test_attrs_by_entity_id(db_client):
    num_updates = 10
    update_entities(db_client, num_updates)

    entity_id = '1-1'
    result = query_all(db_client, DB_NAME, "WHERE entity_id = '{}'".format(entity_id))
    loaded_entities = list(iter_entities(result))
    assert len(loaded_entities) == 1
    assert all(map(lambda e:e['id']==entity_id, loaded_entities))
