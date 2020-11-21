from exceptions.exceptions import AmbiguousNGSIIdError
from translators.base_translator import BaseTranslator
from translators.crate import NGSI_TEXT
from conftest import crate_translator as translator, entity
from utils.common import *
from datetime import datetime, timezone

from src.utils.common import create_random_entities


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
    op = 'select latitude(location), longitude(location) from etroom'
    translator.cursor.execute(op)
    res = translator.cursor.fetchall()
    assert len(res) == 1
    assert res[0] == [19.6389474, -98.9109537]

    entities = translator.query()
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
    entities = translator.query()
    assert len(entities) == 1
    check_notifications_record([entity], entities)

    entity_new = {
        'id': 'Room1',
        'type': 'Room',
        TIME_INDEX_NAME: datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        'temperature': {
            'type': 'Number',
            'value': 19
        }
    }
    translator.insert([entity_new])
    entities = translator.query()
    assert len(entities) == 1

    # Check location's None is saved as a geo_point column in crate
    op = 'select latitude(location), longitude(location), temperature from ' \
         'etroom order by time_index ASC'
    translator.cursor.execute(op)
    res = translator.cursor.fetchall()
    assert len(res) == 2
    assert res[0] == [19.6389474, -98.9109537, None]
    assert res[1] == [None, None, 19]
    translator.clean()

def within_east_hemisphere(e):
    return e["attr_geo"]["values"][0]["coordinates"][0] > 0


def beyond_mid_epoch(e):
    mid_epoch = datetime(1970, 6, 28).isoformat(timespec='milliseconds')
    return e["attr_time"]["values"][0] > mid_epoch
