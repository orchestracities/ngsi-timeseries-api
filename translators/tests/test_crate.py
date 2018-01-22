from conftest import entity
from datetime import datetime
from translators.base_translator import BaseTranslator
from translators.benchmark import benchmark
from translators.crate import NGSI_TEXT
from translators.fixtures import crate_translator as translator
from utils.common import *
import pytest
import statistics


def test_insert(translator):
    entities = create_random_entities(1, 2, 10, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount == len(entities)


def test_insert_entity(translator, entity):
    entity[BaseTranslator.TIME_INDEX_NAME] = datetime.now().isoformat()[:-3]
    result = translator.insert([entity])
    assert result.rowcount == 1

    translator._refresh([entity['type']])

    loaded_entity = translator.query()

    # These 2 can be ignored when empty. TODO: #12 Support attribute metadata
    entity['temperature'].pop('metadata')
    entity['pressure'].pop('metadata')

    assert_ngsi_entity_equals(entity, loaded_entity[0])


def test_insert_multiple_types(translator):
    entities = create_random_entities(num_types=3, num_ids_per_type=2, num_updates=1, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0

    # Again to check metadata handling works fine
    entities = create_random_entities(num_types=3, num_ids_per_type=2, num_updates=1, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0


def test_query_all_before_insert(translator):
    loaded_entities = translator.query()
    assert len(loaded_entities) == 0


def test_query_all(translator):
    entities = create_random_entities(2, 2, 2, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0

    translator._refresh(['0', '1'])

    loaded_entities = translator.query()

    assert len(loaded_entities) == len(entities)
    key = lambda e: e[BaseTranslator.TIME_INDEX_NAME]
    a = sorted(entities, key=key)
    b = sorted(loaded_entities, key=key)
    for e, le in zip(a, b):
        assert_ngsi_entity_equals(e, le)


def test_attrs_by_entity_id(translator):
    # First insert some data
    num_updates = 10
    entities = create_random_entities(1, 2, num_updates, use_time=True, use_geo=True)
    translator.insert(entities)
    translator._refresh(['0'])

    # Now query by entity id
    entity_id = '0-1'
    loaded_entities = translator.query(entity_type='0', entity_id=entity_id)

    assert len(loaded_entities) == num_updates
    assert all(map(lambda e: e['id'] == entity_id, loaded_entities))


WITHIN_EAST_EMISPHERE = "within(attr_geo, 'POLYGON ((0 -90, 180 -90, 180 90, 0 90, 0 -90))')"

@pytest.mark.parametrize("attr_name, clause, tester", [
    ("attr_bool", "= True", lambda e: e["attr_bool"]["value"]),
    ("attr_str", "> 'M'", lambda e: e["attr_str"]["value"] > "M"),
    ("attr_float", "< 0.5", lambda e: e["attr_float"]["value"] < 0.5),
    ("attr_time", "> '1970-06-28T00:00'", lambda e: e["attr_time"]["value"] > datetime(1970, 6, 28).isoformat()[:-3]),
    (WITHIN_EAST_EMISPHERE, "", lambda e: e["attr_geo"]["value"]["coordinates"][0] > 0),
])
def test_query_per_attribute(translator, attr_name, clause, tester):
    num_types = 1
    num_ids_per_type = 2
    num_updates = 10

    entities = create_random_entities(num_types, num_ids_per_type, num_updates, use_time=True, use_geo=True)
    translator.insert(entities)
    translator._refresh(['0'])

    entities = translator.query(entity_type='0', where_clause="where {} {}".format(attr_name, clause))

    total = num_types * num_ids_per_type * num_updates
    assert len(entities) > 0, "No entities where found with the clause: {}{}".format(attr_name, clause)
    assert len(entities) < total, "All entities matched the clause. Not expected from an uniform random distribution"
    assert all(map(tester, entities))


def test_average(translator):
    num_updates = 10
    entities = create_random_entities(2, 2, num_updates, use_time=True, use_geo=True)
    translator.insert(entities)
    translator._refresh(['0', '1'])

    # Per entity_id
    eid = '0-1'
    entity_mean = statistics.mean(e['attr_float']['value'] for e in entities if e['id'] == eid)
    entity_mean_read = translator.average(attr_name='attr_float', entity_type='0', entity_id=eid)
    assert pytest.approx(entity_mean_read) == entity_mean

    # Total
    total_mean = statistics.mean(e['attr_float']['value'] for e in entities)
    total_mean_read = translator.average(attr_name='attr_float')
    assert pytest.approx(total_mean_read) == total_mean


def test_benchmark(translator):
    benchmark(translator, num_types=2, num_ids_per_type=2, num_updates=10, use_geo=False, use_time=False)


def test_benchmark_extended(translator):
    benchmark(translator, num_types=2, num_ids_per_type=2, num_updates=10, use_geo=True, use_time=True)


def test_unsupported_ngsi_type(translator):
    e = {
        "type": "SoMeWeIrDtYpE",
        "id": "sOmEwEiRdId",
        TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
        "foo": {
            "type": "DefinitivelyNotAValidNGSIType",
            "value": "BaR",
        },
    }
    translator.insert([e])
    translator._refresh([e['type']])
    entities = translator.query()
    assert len(entities) == 1
    assert_ngsi_entity_equals(e, entities[0])


def test_missing_type_defaults_string(translator):
    e = {
        "type": "SoMeWeIrDtYpE",
        "id": "sOmEwEiRdId",
        TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
        "foo": {
            "value": "BaR",
        },
    }
    translator.insert([e])
    translator._refresh([e['type']])
    entities = translator.query()
    assert len(entities) == 1
    # Response will include the type
    e["foo"]["type"] = NGSI_TEXT
    assert_ngsi_entity_equals(e, entities[0])


def test_capitals(translator):
    entity_type = "SoMeWeIrDtYpE"
    e = {
        "type": entity_type,
        "id": "sOmEwEiRdId",
        TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
        "Foo": {
            "type": "Text",
            "value": "FoO",
        },
        "bAr": {
            "type": "Text",
            "value": "bAr",
        },
    }
    translator.insert([e])
    translator._refresh([entity_type])
    entities = translator.query()
    assert len(entities) == 1
    assert_ngsi_entity_equals(e, entities[0])

    # If a new attribute comes later, I want it translated as well.
    e2 = e.copy()
    e2['id'] = 'SOmEwEiRdId2'
    e2['NewAttr'] = {"type": "Text", "value": "NewAttrValue!"}
    e2[TIME_INDEX_NAME] = datetime.now().isoformat()[:-3]

    translator.insert([e2])
    translator._refresh([entity_type])
    entities = translator.query()
    assert len(entities) == 2

    assert_ngsi_entity_equals(e2, entities[1])
    # Note that old entity gets None for the new attribute
    e['NewAttr'] = {'type': 'Text', 'value': None}
    assert_ngsi_entity_equals(e, entities[0])


def test_no_time_index(translator):
    """
    The Reporter is responsible for injecting the 'time_index' attribute to the
    entity, but even if for some reason the attribute is not there, there
    should be no problem with the insertion.
    """
    e = {
        'id': 'entityId1',
        'type': 'type1',
        'foo': {'type': 'Text', 'value': "SomeText"}
    }
    translator.insert([e])
    translator._refresh([e['type']])
    assert len(translator.query()) == 1


def test_long_json(translator):
    # Github issue 44
    big_entity = {
        'id': 'entityId1',
        'type': 'type1',
        TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
        'foo': {
            'type': 'Text',
            'value': "SomeTextThatWillGetLong" * 2000
        }
    }
    translator.insert([big_entity])
    translator._refresh([big_entity['type']])

    r = translator.query()
    assert len(r) == 1
    assert_ngsi_entity_equals(big_entity, r[0])


def test_geo_point(translator):
    # Github issue #35: Support geo:point
    entity = {
        'id': 'Room1',
        'type': 'Room',
        TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
        'location': {
            'type': 'geo:point',
            'value': "41.3763726, 2.186447514"
        }
    }
    translator.insert([entity])
    translator._refresh([entity['type']])

    # Check location is saved as a geo_point column in crate
    op = 'select latitude(location), longitude(location) from etroom'
    translator.cursor.execute(op)
    res = translator.cursor.fetchall()
    assert len(res) == 1
    assert res[0] == [41.3763726, 2.186447514]

    entities = translator.query()
    assert len(entities) == 1

    # Check entity is retrieved as it was inserted
    assert_ngsi_entity_equals(entity, entities[0])


def test_structured_value_to_array(translator):
    entity = {
        'id': '8906',
        'type': 'AirQualityObserved',
        TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
        'aqi': {'type': 'Number', 'value': 43},
        'city': {'type': 'Text', 'value': 'Antwerpen'},
        'h': {'type': 'Number', 'value': 93},
        'location': {
            'type': 'geo:point',
            'value': '51.2056589, 4.4180728',
        },
        'measurand': {
            'type': 'StructuredValue',
            'value': ['pm25, 43, ugm3, PM25', 'pm10, 30, ugm3, PM10',
                      'p, 1012, hPa, Pressure']
        },
        'p': {'type': 'Number', 'value': 1012},
        'pm10': {'type': 'Number', 'value': 30},
        'pm25': {'type': 'Number', 'value': 43},
        't': {'type': 'Number', 'value': 8.33}
    }
    translator.insert([entity])
    translator._refresh([entity['type']])

    r = translator.query()
    assert len(r) == 1

    # TODO Github issue 24
    # assert_ngsi_entity_equals(entity, r[0])


################################################################################
# FIWARE DATA MODELS
################################################################################

def test_air_quality_observed(translator, air_quality_observed):
    # Add TIME_INDEX as Reporter would
    air_quality_observed[TIME_INDEX_NAME] = datetime.now().isoformat()[:-3]

    result = translator.insert([air_quality_observed])
    assert result.rowcount > 0
    translator._refresh([air_quality_observed['type']])
    loaded = translator.query()
    assert len(loaded) > 0

    assert_ngsi_entity_equals(air_quality_observed, loaded[0])


def test_traffic_flow_observed(translator, traffic_flow_observed):
    # Add TIME_INDEX as Reporter would
    traffic_flow_observed[TIME_INDEX_NAME] = datetime.now().isoformat()[:-3]

    result = translator.insert([traffic_flow_observed])
    assert result.rowcount > 0
    translator._refresh([traffic_flow_observed['type']])
    loaded = translator.query()
    assert len(loaded) > 0

    assert_ngsi_entity_equals(traffic_flow_observed, loaded[0])
