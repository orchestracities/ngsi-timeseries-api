from translators.benchmark import benchmark
from translators.conftest import influx_translator as translator
from utils.common import *
import statistics


def test_insert(translator):
    entities = create_random_entities(2, 2, 10)
    result = translator.insert(entities)
    assert result


def test_query_all(translator):
    num_types = 2
    num_ids_per_type = 2
    num_updates = 10

    entities = create_random_entities(num_types, num_ids_per_type, num_updates)
    result = translator.insert(entities)
    assert result

    loaded_entities = list(translator.query())
    assert len(loaded_entities) == len(entities) == num_types * num_ids_per_type * num_updates


def test_attrs_by_entity_id(translator):
    num_updates = 10
    entities = create_random_entities(2, 2, num_updates)
    translator.insert(entities)

    entity_id = '1-1'
    loaded_entities = translator.query(entity_id=entity_id)

    assert len(loaded_entities) == num_updates
    assert all(map(lambda e: e['id'] == entity_id, loaded_entities))


def test_attr_by_entity_id(translator):
    num_updates = 10
    entities = create_random_entities(2, 2, num_updates)
    translator.insert(entities)

    entity_id = '1-1'
    attr_name = 'attr_str'
    loaded_entities = translator.query(attr_names=[attr_name], entity_id=entity_id)
    assert len(loaded_entities) == num_updates

    filtered = [x['attr_str']['value'] for x in entities if x['id'] == entity_id]
    assert sorted([x['attr_str']['value'] for x in loaded_entities]) == sorted(filtered)


def test_average(translator):
    num_updates = 10
    entities = create_random_entities(2, 2, num_updates)
    translator.insert(entities)

    # Per entity_id
    eid = '0-1'
    entity_mean = statistics.mean(e['attr_float']['value'] for e in entities if e['id'] == eid)
    entity_mean_read = translator.average(attr_name='attr_float', entity_id=eid)
    assert pytest.approx(entity_mean_read) == entity_mean

    # Total
    total_mean = statistics.mean(e['attr_float']['value'] for e in entities)
    total_mean_read = translator.average(attr_name='attr_float')
    assert pytest.approx(total_mean_read) == total_mean


def test_benchmark(translator):
    # If translators breaks, we want to know.
    benchmark(translator, num_types=2, num_ids_per_type=2, num_updates=10, use_geo=False, use_time=False)
