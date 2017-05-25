from translators.base_translator import BaseTranslator
from translators.benchmark import benchmark
from translators.fixtures import rethink_translator as translator
from utils.common import create_random_entities, assert_ngsi_entity_equals
import pytest
import statistics


def test_insert(translator):
    entities = create_random_entities(2, 2, 10, use_time=True, use_geo=True)
    res = translator.insert(entities)
    assert res['inserted'] == 2 * 2 * 10
    assert res['errors'] == 0


def test_query_all(translator):
    entities = create_random_entities(2, 2, 10, use_time=True, use_geo=True)
    translator.insert(entities)

    loaded_entities = list(translator.query())

    assert len(loaded_entities) == 2 * 2 * 10
    key = lambda e: e[BaseTranslator.TIME_INDEX_NAME]
    for e, le in zip(sorted(entities, key=key), sorted(loaded_entities, key=key)):
        assert_ngsi_entity_equals(e, le)


def test_attrs_by_entity_id(translator):
    # First insert some data
    num_updates = 10
    entities = create_random_entities(2, 2, num_updates, use_time=True, use_geo=True)
    translator.insert(entities)

    # Now query by entity id
    entity_id = '1-1'
    loaded_entities = list(translator.query(entity_id=entity_id))

    assert len(loaded_entities) == num_updates
    assert all(map(lambda e: e['id'] == entity_id, loaded_entities))


def test_average(translator):
    num_updates = 10
    entities = create_random_entities(2, 2, num_updates, use_time=True, use_geo=True)
    translator.insert(entities)

    # Per entity_id
    eid = '0-1'
    attr_name = 'attr_float'
    entity_mean = statistics.mean(e[attr_name]['value'] for e in entities if e['id'] == eid)
    entity_mean_read = translator.average(attr_name=attr_name, entity_id=eid)
    assert pytest.approx(entity_mean_read) == entity_mean

    # Total
    total_mean = statistics.mean(e[attr_name]['value'] for e in entities)
    total_mean_read = translator.average(attr_name=attr_name)
    assert pytest.approx(total_mean_read) == total_mean


def test_benchmark(translator):
    benchmark(translator, num_types=2, num_ids_per_type=2, num_updates=10, use_geo=False, use_time=False)


def test_benchmark_extended(translator):
    benchmark(translator, num_types=2, num_ids_per_type=2, num_updates=10, use_geo=True, use_time=True)
