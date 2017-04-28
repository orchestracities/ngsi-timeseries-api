"""
NGSI:                   Crate:
GeoSimple:
    geo:point,          geo_point
    geo:line,           geo_shape
    geo:box             geo_shape
    geo:polygon         geo_shape
GeoJSON:
    geo:json            geo_shape
"""
from benchmark.common import iter_random_entities
from crate import client
import pytest


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
    :param entities:
    :return:
    """
    for entity in entities:
        entry = {}
        entry['entity_type'] = entity.pop('type')
        entry['entity_id'] = entity.pop('id')
        for k in sorted(entity):
            entry[k] = entity[k]["value"]
        yield tuple(entry[k] for k in sorted(entry))


def test_insert(cursor):
    """
    https://crate.io/docs/reference/sql/dml.html#inserting-data
    """
    create_table(cursor)

    entities = list(iter_random_entities(2, 2, use_time=True, use_geo=True))
    entries = list(iter_crate_entries(entities))

    cursor.executemany("insert into notifications values (?,?,?,?,?,?,?)", entries)
    assert cursor.rowcount == len(entities)


def test_list_entities(cursor):
    create_table(cursor)

    entities = list(iter_random_entities(2, 2, use_time=True, use_geo=True))
    entries = list(iter_crate_entries(entities))

    cursor.executemany("insert into notifications values (?,?,?,?,?,?,?)", entries)
    assert cursor.rowcount == len(entities)

    # Due to eventual consistency, we must refresh after insert before querying right-away
    # https://crate.io/docs/reference/sql/refresh.html
    cursor.execute("refresh table notifications")

    cursor.execute("select * from notifications")
    loaded_entities = cursor.fetchall()
    assert len(entities) == len(loaded_entities)
