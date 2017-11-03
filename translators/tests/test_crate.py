from conftest import entity
from datetime import datetime
from translators.base_translator import BaseTranslator
from translators.benchmark import benchmark
from translators.crate import UnsupportedNGSIType
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

    # These 2 can be ignored when empty. TODO: Support attribute metadata
    entity['temperature'].pop('metadata')
    entity['pressure'].pop('metadata')

    assert_ngsi_entity_equals(entity, loaded_entity[0])


def test_insert_multiple_types(translator):
    entities = create_random_entities(num_types=3, num_ids_per_type=2, num_updates=1, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0


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
        TIME_INDEX_NAME: datetime(1970, 6, 28, 1, 1, 1).isoformat()[:-3],
        "foo": {
            "type": "DefinitivelyNotAValidNGSIType",
            "value": "BaR",
        }
    }
    # Assert exception is raised with error message containing both unsupported given type and supported expected type.
    with pytest.raises(UnsupportedNGSIType, match=r"DefinitivelyNotAValidNGSIType.* Text"):
        translator.insert([e])


def test_capitals(translator):
    e = {
        "type": "SoMeWeIrDtYpE",
        "id": "sOmEwEiRdId",
        TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
        "foo": {
            "type": "Text",
            "value": "BaR",
        }
    }
    translator.insert([e])
    translator._refresh(["SoMeWeIrDtYpE"])
    entities = translator.query()
    assert len(entities) == 1
    assert_ngsi_entity_equals(e, entities[0])


# FIWARE DATA MODELS

def test_air_quality_observed(translator, air_quality_observed):
    # Add TIME_INDEX as Reporter would
    air_quality_observed[TIME_INDEX_NAME] = datetime.now().isoformat()

    result = translator.insert([air_quality_observed])
    assert result.rowcount > 0
    translator._refresh([air_quality_observed['type']])
    loaded = translator.query()
    assert len(loaded) > 0

    assert_ngsi_entity_equals(air_quality_observed, loaded[0])
