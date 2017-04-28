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
from crate import client
from datetime import datetime
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
                        time timestamp primary key, \
                        entity_type string, \
                        entity_id string, \
                        attr_bool boolean, \
                        attr_float float, \
                        attr_str string )")
                        # attr_geo geo_point)")


def test_insert(cursor):
    """
    https://crate.io/docs/reference/sql/dml.html#inserting-data
    """
    create_table(cursor)

    time = datetime.now().isoformat()
    cursor.execute("insert into notifications (time, entity_type, entity_id, attr_bool, attr_float, attr_str) "
                         "values (?,?,?,?,?,?)", (time, "Room", "Room1", True, 3.14, "sala"))

    assert cursor.rowcount == 1  # When insert fails cursor count is decreased by the amount of failed inserts.

    # Due to eventual consistency, we must refresh after insert before querying right-away
    # https://crate.io/docs/reference/sql/refresh.html
    cursor.execute("refresh table notifications")

    cursor.execute("select * from notifications")
    entities = cursor.fetchall()
    assert len(entities) == 1