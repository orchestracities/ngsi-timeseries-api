"""
Test Crate queries that span across multiple entities (of the same type for
now).

Query has historically accepted an entity_id parameter (the id of the entity).

It has been refactored to be called entity_ids and be a list of ids.
For now, having more than one element in this list requires the type to be
specified and unique.
"""
from conftest import crate_translator as translator
from utils.common import create_random_entities


def test_query_multiple_ids(translator):
    # First insert some data
    num_updates = 3
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=4,
                                      num_updates=num_updates)
    translator.insert(entities)
    translator._refresh(['0', '1'])

    loaded_entities = translator.query(entity_type='0',
                                       entity_ids=['0-0', '0-2'])

    assert len(loaded_entities) == 2 * num_updates

    assert any([e['id'] == '0-0' for e in loaded_entities])
    assert any([e['id'] == '0-2' for e in loaded_entities])
    # All results are of type 0 and cannot be of a non-requested id.
    assert all(map(lambda e: e['id'] in ('0-0', '0-2') and e['type'] == '0',
                   loaded_entities))


def test_query_multiple_ids_bak(translator):
    # Should not break old usage of one single entity_id
    num_updates = 3
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=4,
                                      num_updates=num_updates)
    translator.insert(entities)
    translator._refresh(['0', '1'])

    loaded_entities = translator.query(entity_type='0', entity_ids=['0-1'])
    assert len(loaded_entities) == 1 * num_updates
    assert all([e['id'] == '0-1' for e in loaded_entities])


def test_query_multiple_ids_with_invalids(translator):
    # Nonexistent ids should be ignored
    num_updates = 3
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=4,
                                      num_updates=num_updates)
    translator.insert(entities)
    translator._refresh(['0', '1'])

    loaded_entities = translator.query(entity_type='0',
                                       entity_ids=['nonexistent'])
    assert len(loaded_entities) == 0

    loaded_entities = translator.query(entity_type='0',
                                       entity_ids=['0-1', 'nonexistent'])

    assert len(loaded_entities) == 1 * num_updates
