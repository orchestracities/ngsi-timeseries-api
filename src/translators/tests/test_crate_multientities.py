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

    loaded_entities = translator.query(entity_type='0',
                                       entity_ids=['0-0', '0-2'])
    assert len(loaded_entities) == 2

    # All results are of type 0 and cannot be of a non-requested id.
    assert loaded_entities[0]['id'] == '0-0'
    assert loaded_entities[0]['type'] == '0'
    assert loaded_entities[1]['id'] == '0-2'
    assert loaded_entities[1]['type'] == '0'
    translator.clean()


def test_query_multiple_ids_bak(translator):
    # Should not break old usage of one single entity_id
    num_updates = 3
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=4,
                                      num_updates=num_updates)
    translator.insert(entities)

    records = translator.query(entity_type='0', entity_ids=['0-1'])
    assert len(records) == 1
    assert records[0]['id'] == '0-1'
    translator.clean()


def test_query_multiple_ids_with_invalids(translator):
    # Nonexistent ids should be ignored
    num_updates = 3
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=4,
                                      num_updates=num_updates)
    translator.insert(entities)

    loaded_entities = translator.query(entity_type='0',
                                       entity_ids=['nonexistent'])
    assert len(loaded_entities) == 0

    loaded_entities = translator.query(entity_type='0',
                                       entity_ids=['0-1', 'nonexistent'])
    assert len(loaded_entities) == 1
    translator.clean()
