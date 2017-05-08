import statistics

from benchmark.common import *
from crate import client
from datetime import datetime, timedelta
from functools import partial
import pytest
import timeit


# These defaults are to be used with the influx run by the benchmark/docker-compose.yml file.
HOST = "0.0.0.0:4200"
PORT = 4200
DB_NAME = "ngsi-tsdb"


@pytest.fixture
def connection():
    conn = client.connect([HOST], error_trace=True)
    yield conn
    conn.close()


@pytest.fixture()
def cursor(connection):
    cur = connection.cursor()
    create_table(cur)
    yield cur
    cur.close()


def create_table(cursor):
    cursor.execute("DROP TABLE IF EXISTS notifications")
    cursor.execute("create table notifications ( \
                        attr_time timestamp, \
                        entity_type string, \
                        entity_id string, \
                        attr_bool boolean, \
                        attr_float float, \
                        attr_str string, \
                        attr_geo geo_shape)")


def iter_crate_entries(entities):
    """
    :param entities: iterable of dicts (NGSI JSON Entity Representation)
    :return: iterator on crate table entries to be inserted. I.e, NGSI to CrateDB.
    """
    for entity in entities:
        entry = {}
        for k in sorted(entity):
            if k == 'type':
                entry['entity_type'] = entity[k]
            elif k == 'id':
                entry['entity_id'] = entity[k]
            else:
                entry[k] = entity[k]["value"]
        yield tuple(entry[k] for k in sorted(entry))


def iter_entities(results, keys):
    """
    :param results: list(results). The results of a CrateDB fetchall query.
    :param keys: list(unicode). The column names of the results so that NGSI entities can be properly reconstructed.
    :return: Iterator on the list of NGSI entities represented by the given results. I.e, CrateDB results to NGSI
    JSON Entity Representation.
    """
    for r in results:
        entity = {}
        for k, v in zip(keys, r):
            if k == 'entity_type':
                entity['type'] = v
            elif k == 'entity_id':
                entity['id'] = v
            else:
                t = ATTR_TO_TYPE[k]
                entity[k] = {'value': v, 'type': t}

                # From CrateDB docs: Timestamps are always returned as long values
                if t == 'DateTime':
                    utc = datetime(1970, 1, 1, 0, 0, 0, 0) + timedelta(milliseconds=entity[k]['value'])
                    # chopping last 3 digits of microseconds to avoid annoying diffs in testing
                    entity[k]['value'] = utc.isoformat()[:-3]

        assert 'id' in entity
        assert 'type' in entity
        yield entity


def insert(cursor, entities):
    """
    https://crate.io/docs/reference/sql/dml.html#inserting-data
    """
    entries = list(iter_crate_entries(entities))
    cursor.executemany("insert into notifications values (?,?,?,?,?,?,?)", entries)
    return


def insert_random_updates(cursor, num_updates=10, **kwargs):
    """
    This method will create N updates of all the attributes and write them to disk.
    Later, this could be fine-grained to only update specific attributes and/or for specific entities instead of all.

    In CrateDB, attr update means a new table entry. (In InfluxDB it will be a matter of sending a new measurement).
    """
    all_entities = []
    for up in range(num_updates):
        entities = list(iter_random_entities(**kwargs))
        insert(cursor, entities)
        all_entities.extend(entities)
    cursor.execute("refresh table notifications")
    return all_entities


def query(cursor, select="*", table_name="notifications", where_clause=""):
    cursor.execute("select {} from {} {}".format(select, table_name, where_clause))
    return cursor


def average(cursor, entity_id=None):
    """
    :param cursor:
    :param entity_id:
    :return: This will be a simple average among all attr_float values in the records.
    """
    where_clause = "where entity_id = '{}'".format(entity_id) if entity_id else ""
    return query(cursor, select="avg(attr_float)", where_clause=where_clause)


def test_insert(cursor):
    entities = list(iter_random_entities(use_time=True, use_geo=True))
    insert(cursor, entities)
    assert cursor.rowcount == len(entities)


def test_list_entities(cursor):
    entities = list(iter_random_entities(use_time=True, use_geo=True))
    insert(cursor, entities)
    assert cursor.rowcount == len(entities)

    cursor = query(cursor, "*")

    loaded_entries = cursor.fetchall()
    col_names = [x[0] for x in cursor.description]
    loaded_entities = list(iter_entities(loaded_entries, col_names))

    for e, le in zip(sorted(entities, key=entity_pk), sorted(loaded_entities, key=entity_pk)):
        assert_ngsi_entity_equals(e, le)


def test_updates(cursor):
    num_types = 2
    num_ids_per_type = 2
    num_updates = 10
    insert_random_updates(cursor, num_updates, num_types=num_types, num_ids_per_type=num_ids_per_type, use_time=True,
                          use_geo=True)

    cursor = query(cursor, "*")
    assert cursor.rowcount == num_types * num_ids_per_type * num_updates


def test_attrs_by_entity_id(cursor):
    # First insert some data
    num_updates = 10
    insert_random_updates(cursor, num_updates, use_time=True, use_geo=True)

    # Now query by entity id
    entity_id = '1-1'
    cursor = query(cursor, "*", where_clause="where entity_id = '{}'".format(entity_id))

    assert cursor.rowcount == num_updates
    col_names = [x[0] for x in cursor.description]
    entities = list(iter_entities(cursor.fetchall(), col_names))
    assert len(entities) == 10
    assert all(map(lambda e: e['id'] == entity_id, entities))


WITHIN_EAST_EMISPHERE = "within(attr_geo, 'POLYGON ((0 -90, 180 -90, 180 90, 0 90, 0 -90))')"

@pytest.mark.parametrize("attr_name, clause, tester", [
    ("attr_bool", "= True", lambda e: e["attr_bool"]["value"]),
    ("attr_str", "> 'M'", lambda e: e["attr_str"]["value"] > "M"),
    ("attr_float", "< 0.5", lambda e: e["attr_float"]["value"] < 0.5),
    ("attr_time", "> '1970-06-28T00:00'", lambda e: e["attr_time"]["value"] > datetime(1970, 6, 28).isoformat()[:-3]),
    (WITHIN_EAST_EMISPHERE, "", lambda e: e["attr_geo"]["value"]["coordinates"][0] > 0),
])
def test_query_per_attribute(cursor, attr_name, clause, tester):
    num_types = 2
    num_ids_per_type = 2
    num_updates = 10

    insert_random_updates(cursor, num_updates, num_types=num_types, num_ids_per_type=num_ids_per_type,
                          use_time=True, use_geo=True)

    cursor.execute("select * from notifications where {} {}".format(attr_name, clause))

    col_names = [x[0] for x in cursor.description]
    entities = list(iter_entities(cursor.fetchall(), col_names))

    total = num_types * num_ids_per_type * num_updates
    assert len(entities) > 0, "No entities where found with the clause: {}{}".format(attr_name, clause)
    assert len(entities) < total, "All entities matched the clause: {}{}. Not expected from an uniform random distribution"
    assert all(map(tester, entities))


def test_average(cursor):
    entities = insert_random_updates(cursor, num_updates=10, num_types=10, num_ids_per_type=10,
                                     use_time=True, use_geo=True)
    # Per entity_id
    eid = '0-1'
    res = average(cursor, eid)
    avg_read = res.fetchone()[0]
    entity_avg = statistics.mean(e['attr_float']['value'] for e in entities if e['id'] == eid)
    assert pytest.approx(avg_read) == entity_avg

    # Total
    res = average(cursor)
    total_avg_read = res.fetchone()[0]
    total_avg = statistics.mean(e['attr_float']['value'] for e in entities)
    assert pytest.approx(total_avg_read) == total_avg


def test_benchmark(cursor):
    num_types = 10
    num_ids_per_type = 100
    num_entities = num_types * num_ids_per_type

    entities = list(iter_random_entities(num_types=num_types, num_ids_per_type=num_ids_per_type,
                                         use_time=True, use_geo=True))
    assert len(entities) == num_entities

    results = {}

    # Insert 1 entity
    res = timeit.timeit(partial(insert, cursor=cursor, entities=entities[-1:]), number=1, globals=globals())
    results[BM_INSERT_1E] = res

    # Insert N entities
    res = timeit.timeit(partial(insert, cursor=cursor, entities=entities[:-1]), number=1, globals=globals())
    results[BM_INSERT_NE] = res

    # Insert more updates per each entity...
    insert_random_updates(cursor, 10, num_types=num_types, num_ids_per_type=num_ids_per_type,
                          use_time=True, use_geo=True)

    random_id = pick_random_entity_id(num_types, num_ids_per_type)
    where_clause = "WHERE entity_id = '{}'".format(random_id)

    # Query 1 attr of 1 entity
    res = timeit.timeit(partial(query, cursor=cursor,
                                select='attr_str', where_clause=where_clause), number=1, globals=globals())
    results[BM_QUERY_1A1E] = res

    # Query all attrs of 1 entity
    res = timeit.timeit(partial(query, cursor=cursor, where_clause=where_clause), number=1, globals=globals())
    results[BM_QUERY_NA1E] = res

    # Query 1 attr of N entities
    res = timeit.timeit(partial(query, cursor=cursor, select='attr_str'), number=1, globals=globals())
    results[BM_QUERY_1ANE] = res

    # Query all attrs of N entities
    res = timeit.timeit(partial(query, cursor=cursor), number=1, globals=globals())
    results[BM_QUERY_NANE] = res

    # Query aggregate on 1 entity
    res = timeit.timeit(partial(average, cursor=cursor, entity_id=random_id), number=1, globals=globals())
    results[BM_AGGREGATE_1A1E] = res

    # Query aggregate on all entities
    res = timeit.timeit(partial(average, cursor=cursor), number=1, globals=globals())
    results[BM_AGGREGATE_1ANE] = res

    return results
