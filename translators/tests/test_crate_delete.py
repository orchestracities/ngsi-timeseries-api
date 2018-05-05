from datetime import datetime
from translators.fixtures import crate_translator as translator
from utils.common import create_random_entities, TIME_INDEX_NAME


def _refresh_all(translator, entities, fiware_service=None):
    types = set([e['type'] for e in entities])
    translator._refresh(types, fiware_service)


def test_delete_entity_defaults(translator):
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=2,
                                      num_updates=5)
    translator.insert(entities)
    _refresh_all(translator, entities)

    to_delete = entities[0]
    deleted_type = to_delete['type']
    deleted_id = to_delete['id']

    n_total = len(translator.query())
    assert n_total == 2 * 2 * 5

    n_selected = len(translator.query(entity_type=deleted_type,
                                      entity_id=deleted_id))
    assert n_selected == 5

    n_deleted = translator.delete_entity(deleted_id, type=deleted_type)
    assert n_deleted == 5
    _refresh_all(translator, entities)

    remaining = translator.query()
    assert len(remaining) == (n_total - n_deleted)

    survivors = translator.query(entity_type=deleted_type, entity_id=deleted_id)
    assert len(survivors) == 0


def test_delete_entity_customs(translator):
    entities = create_random_entities(num_types=1,
                                      num_ids_per_type=2,
                                      num_updates=10)

    for i, e in enumerate(entities):
        time_index = datetime(2018, 1, 1 + i).isoformat()[:-3]
        e[TIME_INDEX_NAME] = time_index

    translator.insert(entities)
    _refresh_all(translator, entities)

    to_delete = entities[-1]
    deleted_type = to_delete['type']
    deleted_id = to_delete['id']

    res = translator.delete_entity(deleted_id, type=deleted_type,
                                   from_date=datetime(2018, 1, 8).isoformat(),
                                   to_date=datetime(2018, 1, 16).isoformat())
    assert res == 5
    _refresh_all(translator, entities)

    remaining = translator.query()
    assert len(remaining) == 15


def test_delete_entity_with_tenancy(translator):
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=2,
                                      num_updates=5)
    fs = 'fs'
    fsp = 'fsp'
    translator.insert(entities, fiware_service=fs, fiware_servicepath=fsp)
    _refresh_all(translator, entities, fiware_service=fs)

    to_delete = entities[0]
    deleted_type = to_delete['type']
    deleted_id = to_delete['id']
    res = translator.delete_entity(deleted_id, type=deleted_type)
    assert res == 0

    res = translator.delete_entity(deleted_id,
                                   type=deleted_type,
                                   fiware_service=fs)
    assert res == 0
    res = translator.delete_entity(deleted_id,
                                   type=deleted_type,
                                   fiware_service=fs,
                                   fiware_servicepath=fsp)
    assert res == 5


def test_delete_entities_defaults(translator):
    entities = create_random_entities(num_types=3,
                                      num_ids_per_type=2,
                                      num_updates=20)
    translator.insert(entities)
    _refresh_all(translator, entities)

    type_to_delete = entities[0]['type']
    res = translator.delete_entities(type_to_delete)
    assert res == 20 * 2

    remaining = translator.query()
    assert len(remaining) == 20 * 2 * (3-1)
    assert all([r['type'] != type_to_delete for r in remaining])


def test_delete_entities_customs(translator):
    entities = create_random_entities(num_types=4,
                                      num_ids_per_type=1,
                                      num_updates=4)
    for i, e in enumerate(entities):
        time_index = datetime(2018, 1, 1 + i).isoformat()[:-3]
        e[TIME_INDEX_NAME] = time_index

    translator.insert(entities)
    _refresh_all(translator, entities)

    type_to_delete = entities[-1]['type']
    res = translator.delete_entities(type_to_delete,
                                     from_date=datetime(2018, 1, 4).isoformat(),
                                     to_date=datetime(2018, 1, 12).isoformat())
    assert res == 3
    _refresh_all(translator, entities)

    remaining = translator.query()
    assert len(remaining) == 4 * 4 - 3


def test_delete_entities_with_tenancy(translator):
    fs = 'fs'
    fsp = 'fsp'
    entities = create_random_entities(num_types=3,
                                      num_ids_per_type=1,
                                      num_updates=10)
    translator.insert(entities, fiware_service=fs, fiware_servicepath=fsp)
    _refresh_all(translator, entities, fiware_service=fs)

    type_to_delete = entities[0]['type']
    res = translator.delete_entities(type_to_delete)
    assert res == 0

    res = translator.delete_entities(type_to_delete,
                                     fiware_service=fs,
                                     fiware_servicepath='another/path')
    assert res == 0

    res = translator.delete_entities(type_to_delete,
                                     fiware_service=fs,
                                     fiware_servicepath=fsp)
    assert res == 10
