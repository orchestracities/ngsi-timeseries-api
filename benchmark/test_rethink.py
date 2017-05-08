import statistics
import timeit
from functools import partial

import pytest
import rethinkdb as rt

from benchmark.common import iter_random_entities, entity_pk, assert_ngsi_entity_equals, ATTR_TO_TYPE, BM_INSERT_1E, \
    BM_INSERT_NE, pick_random_entity_id, BM_QUERY_1A1E, BM_QUERY_NA1E, BM_QUERY_NANE, BM_AGGREGATE_1A1E, \
    BM_AGGREGATE_1ANE, BM_QUERY_1ANE

HOST = "0.0.0.0"
PORT = 28015
DB_NAME = "test"  # Rethink goes with this db by default to simplify all calls in testing usecases.
TABLE_NAME = "notifications"


@pytest.fixture()
def connection():
    conn = rt.connect(HOST, PORT)

    res = rt.db(DB_NAME).table_create(TABLE_NAME).run(conn)
    assert res['tables_created'] == 1

    yield conn

    rt.db(DB_NAME).table_drop(TABLE_NAME).run(conn)
    conn.close()


def iter_rethink_entries(entities):
    """
    :param entities: iterable of dicts (NGSI JSON Entity Representation)
    :return: iterator on rethink entries to be inserted. I.e, NGSI to RethinkDB.
    """
    for entity in entities:
        entry = {}
        for k in entity:
            if k == 'type':
                entry['entity_type'] = entity[k]
            elif k == 'id':
                entry['entity_id'] = entity[k]
            else:
                entry[k] = entity[k]["value"]
        yield entry


def iter_entities(entries):
    """
    :return: Iterator on the list of NGSI entities represented by the given results. I.e, RethinkDB results to NGSI
    JSON Entity Representation.
    """
    for e in entries:
        entity = {}
        for k, v in e.items():
            if k == 'id':
                # RethinkDB gives an id to each object, which we ignore for now.
                continue
            elif k == 'entity_type':
                entity['type'] = v
            elif k == 'entity_id':
                entity['id'] = v
            else:
                t = ATTR_TO_TYPE[k]
                entity[k] = {'value': v, 'type': t}
        yield entity


def insert(connection, entities):
    """
    https://rethinkdb.com/api/python/#insert

    :param connection:
    :param entities:
    :return:
    """
    op = rt.table(TABLE_NAME).insert(iter_rethink_entries(entities))
    res = op.run(connection)
    return res


def insert_random_updates(connection, num_updates=10, **kwargs):
    """
    This method will create N updates of all the attributes and write them to disk.
    Later, this could be fine-grained to only update specific attributes and/or for specific entities instead of all.

    Attr update means a new table entry.
    """
    all_entities = []
    for up in range(num_updates):
        entities = list(iter_random_entities(**kwargs))
        insert(connection, entities)
        all_entities.extend(entities)
    return all_entities


def query(connection, attr_names=None, entity_id=None):
    """
    :param connection:
    :return: For now, a query all.
    """
    op = rt.table(TABLE_NAME)
    if attr_names:
        op = op.pluck(attr_names)
    if entity_id:
        op = op.filter(lambda x: rt.branch(x['entity_id'] == entity_id, True, False))
    res = op.run(connection)
    return res


def average(connection, entity_id=None):
    """
    :param connection:
    :param entity_id:
    :return: This will be a simple average among all attr_float values in the records.
    """
    if entity_id:
        op = rt.table(TABLE_NAME).filter({'entity_id': entity_id}).avg('attr_float')
    else:
        op = rt.table(TABLE_NAME).avg('attr_float')
    res = op.run(connection)
    return res


def test_insert(connection):
    entities = list(iter_random_entities(use_time=True, use_geo=True))
    res = insert(connection, entities)
    assert res['inserted'] == 4
    assert res['errors'] == 0


def test_list_entities(connection):
    entities = list(iter_random_entities(use_time=True, use_geo=True))
    insert(connection, entities)

    res = query(connection)
    loaded_entities = list(iter_entities(res))

    for e, le in zip(sorted(entities, key=entity_pk), sorted(loaded_entities, key=entity_pk)):
        assert_ngsi_entity_equals(e, le)


def test_attrs_by_entity_id(connection):
    # First insert some data
    num_updates = 10
    insert_random_updates(connection, num_updates, use_time=True, use_geo=True)

    # Now query by entity id
    entity_id = '1-1'
    res = query(connection, entity_id=entity_id)
    entities = list(iter_entities(res))
    assert len(entities) == 10
    assert all(map(lambda e: e['id'] == '1-1', entities))


def test_average(connection):
    entities = insert_random_updates(connection, num_updates=10, num_types=10, num_ids_per_type=10,
                                     use_time=True, use_geo=True)
    # Per entity_id
    eid = '0-1'
    avg_read = average(connection, eid)
    entity_avg = statistics.mean(e['attr_float']['value'] for e in entities if e['id'] == eid)
    assert pytest.approx(avg_read) == entity_avg

    # Total
    total_avg_read = average(connection)
    total_avg = statistics.mean(e['attr_float']['value'] for e in entities)
    assert pytest.approx(total_avg_read) == total_avg


def test_benchmark(connection):
    num_types = 10
    num_ids_per_type = 100
    num_entities = num_types * num_ids_per_type

    entities = list(iter_random_entities(num_types=num_types, num_ids_per_type=num_ids_per_type,
                                         use_time=True, use_geo=True))
    assert len(entities) == num_entities

    results = {}

    # Insert 1 entity
    res = timeit.timeit(partial(insert, connection=connection, entities=entities[-1:]), number=1, globals=globals())
    results[BM_INSERT_1E] = res

    # Insert N entities
    res = timeit.timeit(partial(insert, connection=connection, entities=entities[:-1]), number=1, globals=globals())
    results[BM_INSERT_NE] = res

    # Insert more updates per each entity...
    insert_random_updates(connection, 10, num_types=num_types, num_ids_per_type=num_ids_per_type,
                          use_time=True, use_geo=True)

    random_id = pick_random_entity_id(num_types, num_ids_per_type)

    # Query 1 attr of 1 entity
    res = timeit.timeit(partial(query, connection=connection,
                                attr_names=['attr_str'], entity_id=random_id), number=1, globals=globals())
    results[BM_QUERY_1A1E] = res

    # Query all attrs of 1 entity
    res = timeit.timeit(partial(query, connection=connection, entity_id=random_id), number=1, globals=globals())
    results[BM_QUERY_NA1E] = res

    # Query 1 attr of N entities
    res = timeit.timeit(partial(query, connection=connection, attr_names=['attr_str']), number=1, globals=globals())
    results[BM_QUERY_1ANE] = res

    # Query all attrs of N entities
    res = timeit.timeit(partial(query, connection=connection), number=1, globals=globals())
    results[BM_QUERY_NANE] = res

    # Query aggregate on 1 entity
    res = timeit.timeit(partial(average, connection=connection, entity_id=random_id), number=1, globals=globals())
    results[BM_AGGREGATE_1A1E] = res

    # Query aggregate on all entities
    res = timeit.timeit(partial(average, connection=connection), number=1, globals=globals())
    results[BM_AGGREGATE_1ANE] = res

    return results
