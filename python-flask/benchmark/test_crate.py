from benchmark.common import iter_random_entities, ATTR_TO_TYPE, entity_pk, assert_ngsi_entity_equals
from crate import client
from datetime import datetime, timedelta
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


def test_insert(cursor):
    """
    https://crate.io/docs/reference/sql/dml.html#inserting-data
    """
    entities = list(iter_random_entities(use_time=True, use_geo=True))
    entries = list(iter_crate_entries(entities))

    cursor.executemany("insert into notifications values (?,?,?,?,?,?,?)", entries)
    assert cursor.rowcount == len(entities)


def test_list_entities(cursor):
    entities = list(iter_random_entities(use_time=True, use_geo=True))
    entries = list(iter_crate_entries(entities))

    cursor.executemany("insert into notifications values (?,?,?,?,?,?,?)", entries)
    assert cursor.rowcount == len(entities)

    # Due to eventual consistency, we must refresh after insert before querying right-away
    # https://crate.io/docs/reference/sql/refresh.html
    cursor.execute("refresh table notifications")
    cursor.execute("select * from notifications")

    loaded_entries = cursor.fetchall()
    col_names = [x[0] for x in cursor.description]
    loaded_entities = list(iter_entities(loaded_entries, col_names))

    for e, le in zip(sorted(entities, key=entity_pk), sorted(loaded_entities, key=entity_pk)):
        assert_ngsi_entity_equals(e, le)


def update_entities(cursor, num_updates=10, **kwargs):
    """
    This method will create N updates of all the attributes and write them to disk.
    Later, this could be fine-grained to only update specific attributes and/or for specific entities instead of all.

    In CrateDB, attr update means a new table entry. (In InfluxDB it will be a matter of sending a new measurement).
    """
    for up in range(num_updates):
        for entity in iter_crate_entries(iter_random_entities(**kwargs)):
            cursor.execute("insert into notifications values (?,?,?,?,?,?,?)", entity)


def test_updates(cursor):
    num_types = 2
    num_ids_per_type = 2
    num_updates = 10

    update_entities(cursor, num_updates, num_types=num_types, num_ids_per_type=num_ids_per_type, use_time=True,
                    use_geo=True)
    cursor.execute("refresh table notifications")

    cursor.execute("select * from notifications")
    assert cursor.rowcount == num_types * num_ids_per_type * num_updates