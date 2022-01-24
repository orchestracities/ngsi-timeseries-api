from datetime import datetime, timezone
import pg8000
import pytest
import random
from time import sleep

from geocoding.geojson.wktcodec import decode_wkb_hexstr
from translators.base_translator import TIME_INDEX_NAME
from translators.timescale import postgres_translator_instance,\
    PostgresConnectionData
from translators.sql_translator import METADATA_TABLE_NAME,\
    TYPE_PREFIX, TENANT_PREFIX, FIWARE_SERVICEPATH

#
# NOTE. Using (sort of) unique IDs to avoid having to clean the DB after each
# test, which slows the whole test suite down to snail pace.
#


def gen_entity_id(entity_type):
    eid = random.randint(1, 2**32)
    return f'{entity_type}:{eid}'


def next_iso_time():
    sleep(0.01)
    return datetime.now(timezone.utc).isoformat()


def add_eid_and_timex(entity):
    etype = entity['type']
    entity['id'] = gen_entity_id(etype)
    entity[TIME_INDEX_NAME] = next_iso_time()


def gen_entity(entity_type):
    return {
        'id': gen_entity_id(entity_type),
        'type': entity_type,
        TIME_INDEX_NAME: next_iso_time(),
        'a_number': {
            'type': 'Number',
            'value': 50.12
        },
        'an_integer': {
            'type': 'Integer',
            'value': 50
        },
        'a_bool': {
            'type': 'Boolean',
            'value': 'true'
        },
        'a_datetime': {
            'type': 'DateTime',
            'value': '2019-07-22T11:46:45.123Z'
        },
        'a_point': {
            'type': 'geo:point',
            'value': '2, 1'
        },
        'a_geom': {
            'type': 'geo:json',
            'value': {
                'type': 'LineString',
                'coordinates': [[30, 10], [10, 30], [40, 40]]
            }
        },
        'a_text': {
            'value': 'no type => text'
        },
        'an_obj': {
            'type': 'Custom',
            'value': {
                'h': 'unknown type && dict value => structured value'
            }
        },
        'an_array': {
            'type': 'StructuredValue',
            'value': [1, 'x', {'v': 'y'}]
        }
    }


def assert_inserted_entity_values(entity, row):
    assert entity['id'] == row['entity_id']
    assert entity['type'] == row['entity_type']
    assert row[TIME_INDEX_NAME].isoformat().startswith(entity[TIME_INDEX_NAME])
    assert entity['a_number']['value'] == row['a_number']
    assert entity['an_integer']['value'] == row['an_integer']
    assert bool(entity['a_bool']['value']) == row['a_bool']
    assert row['a_datetime'] == datetime(2019, 7, 22, 11, 46, 45, 123000,
                                         tzinfo=timezone.utc)
    assert decode_wkb_hexstr(row['a_point']) == {
        'type': 'Point',
        'coordinates': [1.0, 2.0]  # note how lat/lon get swapped
    }
    assert entity['a_geom']['value'] == decode_wkb_hexstr(row['a_geom'])
    assert entity['a_text']['value'] == row['a_text']
    assert entity['an_obj']['value'] == row['an_obj']
    assert entity['an_array']['value'] == row['an_array']


def expected_entity_attrs_meta():
    return {
        'entity_id': ['id', 'Text'],
        'entity_type': ['type', 'Text'],
        TIME_INDEX_NAME: ['time_index', 'DateTime'],
        'a_number': ['a_number', 'Number'],
        'an_integer': ['an_integer', 'Integer'],
        'a_bool': ['a_bool', 'Boolean'],
        'a_datetime': ['a_datetime', 'DateTime'],
        'a_point': ['a_point', 'geo:point'],
        'a_geom': ['a_geom', 'geo:json'],
        'a_text': ['a_text', 'Text'],
        'an_obj': ['an_obj', 'Custom'],
        'an_array': ['an_array', 'StructuredValue']
    }


def insert(entities, fw_svc=None, fw_path=None):
    with postgres_translator_instance() as trans:
        trans.insert(entities, fw_svc, fw_path)


@pytest.fixture(scope='module')
def with_pg8000():
    pg8000.paramstyle = "qmark"
    t = PostgresConnectionData()
    t.read_env()

    pg_conn = pg8000.connect(host=t.host, port=t.port,
                             database=t.db_name,
                             user=t.db_user, password=t.db_pass)
    pg_conn.autocommit = True
    pg_cursor = pg_conn.cursor()

    yield (pg_conn, pg_cursor)

    pg_cursor.close()
    pg_conn.close()


def select_entity_attrs_meta(pg_cursor, full_table_name):
    mdt = METADATA_TABLE_NAME
    stmt = f'select entity_attrs from {mdt} where table_name = ?'
    pg_cursor.execute(stmt, [full_table_name])
    rows = pg_cursor.fetchall()
    return rows[0][0] if rows else {}


def select_hyper_table(pg_cursor, schema_name, table_name):
    stmt = '''select 1 from _timescaledb_catalog.hypertable
              where schema_name = ? and table_name = ?
    '''
    pg_cursor.execute(stmt, [schema_name, table_name])
    rows = pg_cursor.fetchall()
    return rows[0][0] if rows else {}


def select_eid_index(pg_cursor, full_table_name):
    stmt = 'select count(*) from pg_class where relname = ?'
    unquoted_ftn = full_table_name.replace('"', '')
    ix_name = f'ix_{unquoted_ftn}_eid_and_tx'
    pg_cursor.execute(stmt, [ix_name])
    rows = pg_cursor.fetchall()
    return rows[0][0] if rows else {}


def select_entities(pg_cursor, full_table_name, entity_id):
    stmt = f'select * from {full_table_name} where entity_id = ?'

    rows = pg_cursor.execute(stmt, [entity_id])
    keys = [k[0] for k in pg_cursor.description]
    return [dict(zip(keys, row)) for row in rows]


def assert_entity_attrs_meta(pg_cursor, full_table_name):
    data = select_entity_attrs_meta(pg_cursor, full_table_name)
    assert data == expected_entity_attrs_meta()


def assert_have_hyper_table(pg_cursor, schema_name, table_name):
    data = select_hyper_table(pg_cursor, schema_name, table_name)
    assert data == 1


def assert_have_eid_index(pg_cursor, full_table_name):
    data = select_eid_index(pg_cursor, full_table_name)
    assert data == 1


def test_bare_entity(with_pg8000):
    entity_type = 'test-device'
    entity = gen_entity('test-device')
    insert([entity])

    _, pg_cursor = with_pg8000
    full_table_name = f'"{TYPE_PREFIX}{entity_type}"'

    assert_have_hyper_table(pg_cursor, 'public', f'{TYPE_PREFIX}{entity_type}')
    # NOTE. In the hypertable names get unquoted.

    assert_have_eid_index(pg_cursor, full_table_name)
    # NOTE. Translator unquotes schema and table names when creating the ix.

    assert_entity_attrs_meta(pg_cursor, full_table_name)

    rows = select_entities(pg_cursor, full_table_name, entity['id'])
    assert pg_cursor.rowcount == 1
    assert_inserted_entity_values(entity, rows[0])


def test_tenants_entity(with_pg8000):
    entity_type = 'test-device'
    entity = gen_entity('test-device')
    fw_svc, fw_path = 'tenant', '/some/service'
    insert([entity], fw_svc=fw_svc, fw_path=fw_path)

    _, pg_cursor = with_pg8000
    full_table_name = f'"{TENANT_PREFIX}{fw_svc}"."{TYPE_PREFIX}{entity_type}"'

    assert_have_hyper_table(pg_cursor,
                            f'{TENANT_PREFIX}{fw_svc}',
                            f'{TYPE_PREFIX}{entity_type}')
    # NOTE. In the hypertable names get unquoted.

    assert_have_eid_index(pg_cursor, full_table_name)
    # NOTE. Translator unquotes schema and table names when creating the ix.

    assert_entity_attrs_meta(pg_cursor, full_table_name)

    rows = select_entities(pg_cursor, full_table_name, entity['id'])
    assert pg_cursor.rowcount == 1
    assert_inserted_entity_values(entity, rows[0])
    assert rows[0][FIWARE_SERVICEPATH] == fw_path
