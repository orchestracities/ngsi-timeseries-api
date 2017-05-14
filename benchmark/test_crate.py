from benchmark.benchmark import benchmark
from benchmark.common import *
from benchmark.fixtures import crate_translator as translator
from datetime import datetime
import pytest
import statistics


def test_insert(translator):
    entities = create_random_entities(2, 2, 10, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount == len(entities)


def test_query_all(translator):
    entities = create_random_entities(2, 2, 10, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount == len(entities)

    loaded_entities = translator.query()

    key = lambda e: e[BaseTranslator.TIME_INDEX_NAME]
    for e, le in zip(sorted(entities, key=key), sorted(loaded_entities, key=key)):
        assert_ngsi_entity_equals(e, le)


def test_attrs_by_entity_id(translator):
    # First insert some data
    num_updates = 10
    entities = create_random_entities(2, 2, num_updates, use_time=True, use_geo=True)
    translator.insert(entities)
    translator.refresh()

    # Now query by entity id
    entity_id = '1-1'
    loaded_entities = translator.query(entity_id=entity_id)

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
    num_types = 2
    num_ids_per_type = 2
    num_updates = 10

    entities = create_random_entities(num_types, num_ids_per_type, num_updates, use_time=True, use_geo=True)
    translator.insert(entities)
    translator.refresh()

    entities = translator.query(where_clause="where {} {}".format(attr_name, clause))

    total = num_types * num_ids_per_type * num_updates
    assert len(entities) > 0, "No entities where found with the clause: {}{}".format(attr_name, clause)
    assert len(entities) < total, "All entities matched the clause. Not expected from an uniform random distribution"
    assert all(map(tester, entities))


def test_average(translator):
    num_updates = 10
    entities = create_random_entities(2, 2, num_updates, use_time=True, use_geo=True)
    translator.insert(entities)
    translator.refresh()

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
    benchmark(translator, num_types=2, num_ids_per_type=2, num_updates=10, use_geo=False, use_time=False)


def test_2benchmark_extended(translator):
    benchmark(translator, num_types=2, num_ids_per_type=2, num_updates=10, use_geo=True, use_time=True)
