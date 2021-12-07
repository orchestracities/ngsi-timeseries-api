from translators.sql_translator import METADATA_TABLE_NAME, TYPE_PREFIX
from conftest import crate_translator as translator, entity
from utils.common import TIME_INDEX_NAME
from utils.tests.common import *
from datetime import datetime, timezone


def test_db_version(translator):
    version = translator.get_db_version()
    major = int(version.split('.')[0])
    assert major >= 3


def test_geo_point(translator):
    # Github issue #35: Support geo:point
    entity = {
        'id': 'Room1',
        'type': 'Room',
        TIME_INDEX_NAME: datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        'location': {
            'type': 'geo:point',
            'value': "19.6389474, -98.9109537"  # lat, long
        }
    }
    translator.insert([entity])

    # Check location is saved as a geo_point column in crate

    op = "select latitude(_doc['location']), longitude(_doc['location']) " \
         "from etroom "
    translator.cursor.execute(op)
    res = translator.cursor.fetchall()
    assert len(res) == 1
    assert res[0] == [19.6389474, -98.9109537]

    entities, err = translator.query()
    assert len(entities) == 1

    # Check entity is retrieved as it was inserted
    check_notifications_record([entity], entities)
    translator.clean()


def test_geo_point_null_values(translator):
    # Github PR #198: Support geo:point null values
    entity = {
        'id': 'Room1',
        'type': 'Room',
        TIME_INDEX_NAME: datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        'location': {
            'type': 'geo:point',
            'value': "19.6389474, -98.9109537"  # lat, long
        }
    }
    translator.insert([entity])
    entities, err = translator.query()
    assert len(entities) == 1
    check_notifications_record([entity], entities)

    entity_new = {
        'id': 'Room1',
        'type': 'Room',
        TIME_INDEX_NAME: datetime.now(
            timezone.utc).isoformat(
            timespec='milliseconds'),
        'temperature': {
            'type': 'Number',
            'value': 19}}
    translator.insert([entity_new])
    entities, err = translator.query()
    assert len(entities) == 1

    # Check location's None is saved as a geo_point column in crate
    op = "select latitude(_doc['location']), longitude(_doc['location']), temperature from " \
         "etroom order by time_index ASC"
    translator.cursor.execute(op)
    res = translator.cursor.fetchall()
    assert len(res) == 2
    assert res[0] == [19.6389474, -98.9109537, None]
    assert res[1] == [None, None, 19]
    translator.clean()


def test_default_replication(translator):
    """
    By default there should be 2-all replicas

    https://crate.io/docs/crate/reference/en/latest/general/ddl/replication.html
    """
    entities = create_random_entities(1, 2, 10)
    entity = entities[0]
    e_type = entity['type']

    translator.insert(entities)

    et = '{}{}'.format(TYPE_PREFIX, e_type.lower())
    # same as in translator._et2tn but without double quotes
    op = "select number_of_replicas from information_schema.tables where " \
         "table_name = '{}'"
    translator.cursor.execute(op.format(et))
    res = translator.cursor.fetchall()
    assert res[0] == ['2-all']

    # Metadata table should also be replicated
    translator.cursor.execute(op.format(METADATA_TABLE_NAME))
    res = translator.cursor.fetchall()
    assert res[0] == ['2-all']
    translator.clean()
