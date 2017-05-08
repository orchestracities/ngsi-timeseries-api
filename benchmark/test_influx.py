from benchmark.common import *
from functools import partial
from influxdb import InfluxDBClient
import pytest
import statistics
import timeit


# These defaults are to be used with the influx run by the benchmark/docker-compose.yml file.
INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
DB_NAME = "ngsi-tsdb"


@pytest.fixture
def db_client():
    # TODO: Test with DataFrameClient maybe?
    client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, 'root', 'root')
    client.create_database(DB_NAME)
    yield client
    client.drop_database(DB_NAME)


def iter_influx_points(entities):
    """
    :param entities: iterable of dicts (NGSI JSON Entity Representation)
    :return: iterator on InfluxDB JSON representation of measurement points. I.e, NGSI to InfluxDB.
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


def insert(db_client, entities):
    """
    :param db_client:
    :param entities:
    :return: result of write_points call
    """
    points = list(iter_influx_points(entities))
    result = db_client.write_points(points, database=DB_NAME)
    return result


def insert_random_updates(db_client, num_types=2, num_ids_per_type=2, num_updates=10):
    """
    :param db_client:
    :param num_types:
    :param num_ids_per_type:
    :param num_updates:
    :return:
    """
    all_entities = []
    for u in range(num_updates):
        entities = list(iter_random_entities(num_types=num_types, num_ids_per_type=num_ids_per_type))
        insert(db_client, entities)
        all_entities.extend(entities)
    return all_entities


def query(db_client, db_name, select="*", measurements=None, where_clause=""):
    """
    Helper to query entity data from InfluxDB, "gathering" data from given measurements.
    If you want specific NGSI attrs, use the measurements param.
    If you want specific NGSI entities, use the where_clause param.

    :param db_client:
    :param db_name:
    :param select:
    :param measurements: The list of measurements (ngsi attribute names).
    :type measurements: list(unicode)

    :param unicode where_clause: Used to filter. Defaults to empty, so if used, include the WHERE prefix as shown.
    E.g: where_clause = "WHERE entity_id = '1'"
    """
    if not measurements:
        rs = db_client.query("SHOW MEASUREMENTS", database=db_name)
        measurements = [m[0] for m in rs.raw['series'][0]['values']]

    # Be careful when selecting multiple measurements in the same query. If fields names are the same, influxDB will not
    # automatically rename those columns, it will preserve only one.
    query = ""
    for m in measurements:
        query += "select {} from {} {};".format(select, m, where_clause)

    result = db_client.query(query, database=db_name)
    return result


def average(db_client, db_name, entity_id=None):
    """
    There are many types of averages:
        - historical for 1 entity
        - historical for N entities
        - last measurement value for N entities
    This will be a simple average among all attr_float values in the records.
    :param db_client:
    :param db_name:
    :param entity_id: (optional). If given, calculates the average only for the matching entity_id.
    :return:
    """
    clause = "WHERE entity_id = '{}'".format(entity_id) if entity_id else ''
    res = query(db_client, db_name, select='MEAN("value")', measurements=['attr_float'], where_clause=clause)
    return res


def test_insert(db_client):
    """
    https://docs.influxdata.com/influxdb/v1.2/guides/writing_data/
    """
    result = insert(db_client, iter_random_entities())
    assert result


def test_insert_random_updates(db_client):
    types = 2
    ids = 2
    updates = 10
    insert_random_updates(db_client, types, ids, updates)

    result = query(db_client, DB_NAME)
    assert len(result) == 3, "3 measurements for now"
    for r in result:
        points = list(r.get_points())
        assert len(points) == types * ids * updates


def test_query(db_client):
    """
    When querying InfluxDB, remember that there must be at least one field in the select to get results, using only
    time/tags will not return data.

    Queries in Influx are done first by measurement, then of course you can filter.

    More info: https://docs.influxdata.com/influxdb/v1.2/query_language/data_exploration/
    """
    entities = list(iter_random_entities())
    result = insert(db_client, entities)
    assert result

    # For testing purposes, let's get all entities back (querying across multiple measurements)
    result = query(db_client, DB_NAME)
    assert len(result) == 3

    loaded_entities = list(iter_entities(result))
    assert sorted(loaded_entities, key=entity_pk) == sorted(entities, key=entity_pk)


def test_attrs_by_entity_id(db_client):
    insert_random_updates(db_client, num_updates=10)

    entity_id = '1-1'
    result = query(db_client, DB_NAME, where_clause="WHERE entity_id = '{}'".format(entity_id))
    loaded_entities = list(iter_entities(result))
    assert len(loaded_entities) == 1
    assert all(map(lambda e: e['id'] == entity_id, loaded_entities))


def test_average(db_client):
    entities = insert_random_updates(db_client, num_updates=10)

    # Per entity_id
    eid = '0-1'
    entity_mean = statistics.mean(e['attr_float']['value'] for e in entities if e['id'] == eid)
    res = average(db_client, DB_NAME, entity_id=eid)
    entity_mean_read = list(res.get_points())[0]['mean']
    assert pytest.approx(entity_mean_read) == entity_mean

    # Total
    total_mean = statistics.mean(e['attr_float']['value'] for e in entities)
    res = average(db_client, DB_NAME)
    total_mean_read = list(res.get_points())[0]['mean']
    assert pytest.approx(total_mean_read) == total_mean


def test_benchmark(db_client):
    """
    Measure times of each benchmark operation and plot results.
    """
    num_types = 10
    num_ids_per_type = 100
    num_entities = num_types * num_ids_per_type

    entities = list(iter_random_entities(num_types=num_types, num_ids_per_type=num_ids_per_type))
    assert len(entities) == num_entities

    results = {}

    # Insert 1 entity
    res = timeit.timeit(partial(insert, db_client=db_client, entities=entities[-1:]), number=1, globals=globals())
    results[BM_INSERT_1E] = res

    # Insert N entities
    res = timeit.timeit(partial(insert, db_client=db_client, entities=entities[:-1]), number=1, globals=globals())
    results[BM_INSERT_NE] = res

    # Insert more updates per each entity...
    insert_random_updates(db_client, num_types, num_ids_per_type, 10)

    # Query 1 attr of 1 entity
    random_id = pick_random_entity_id(num_types, num_ids_per_type)
    where_clause = "WHERE entity_id = '{}'".format(random_id)
    res = timeit.timeit(partial(query, db_client=db_client, db_name=DB_NAME,
                                measurements=['attr_str'], where_clause=where_clause), number=1, globals=globals())
    results[BM_QUERY_1A1E] = res

    # Query all attrs of 1 entity
    res = timeit.timeit(partial(query, db_client=db_client, db_name=DB_NAME,
                                where_clause=where_clause), number=1, globals=globals())
    results[BM_QUERY_NA1E] = res

    # Query 1 attr of N entities
    res = timeit.timeit(partial(query, db_client=db_client, db_name=DB_NAME,
                                measurements=['attr_str']), number=1, globals=globals())
    results[BM_QUERY_1ANE] = res

    # Query all attrs of N entities
    res = timeit.timeit(partial(query, db_client=db_client, db_name=DB_NAME), number=1, globals=globals())
    results[BM_QUERY_NANE] = res

    # Query aggregate on 1 entity (Needs multiple inserts for the same entity)
    res = timeit.timeit(partial(average, db_client=db_client, db_name=DB_NAME,
                                entity_id=random_id), number=1, globals=globals())
    results[BM_AGGREGATE_1A1E] = res

    # Query aggregate on all entities
    res = timeit.timeit(partial(average, db_client=db_client, db_name=DB_NAME), number=1, globals=globals())
    results[BM_AGGREGATE_1ANE] = res

    return results
