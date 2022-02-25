# To test a single translator use the -k parameter followed by either
# timescale or crate.
# See https://docs.pytest.org/en/stable/example/parametrize.html

from datetime import datetime
from conftest import crate_translator, timescale_translator
from utils.common import TIME_INDEX_NAME
from utils.tests.common import create_random_entities
import pytest


translators = [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
]


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_delete_entity_defaults(translator):
    num_types = 2
    num_ids_per_type = 2
    num_updates = 5

    entities = create_random_entities(num_types, num_ids_per_type, num_updates)
    translator.insert(entities)

    deleted_type = entities[0]['type']
    deleted_id = entities[0]['id']

    total, err = translator.query()
    assert len(total) == num_types * num_ids_per_type

    selected, err = translator.query(
        entity_type=deleted_type, entity_id=deleted_id)
    assert len(selected[0]['index']) == num_updates

    n_deleted = translator.delete_entity(deleted_id, entity_type=deleted_type)
    assert n_deleted == num_updates

    remaining, err = translator.query()
    assert len(remaining) == (len(total) - 1)

    survivors, err = translator.query(
        entity_type=deleted_type, entity_id=deleted_id)
    assert len(survivors) == 0
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_delete_entity_customs(translator):
    entities = create_random_entities(num_types=1,
                                      num_ids_per_type=2,
                                      num_updates=10)
    for i, e in enumerate(entities):
        t = datetime(2018, 1, 1 + i).isoformat(timespec='milliseconds')
        e[TIME_INDEX_NAME] = t

    translator.insert(entities)

    deleted_type = entities[-1]['type']
    deleted_id = entities[-1]['id']

    res = translator.delete_entity(entity_id=deleted_id,
                                   entity_type=deleted_type,
                                   from_date=datetime(2018, 1, 8).isoformat(),
                                   to_date=datetime(2018, 1, 16).isoformat())
    assert res == 5

    affected, err = translator.query(
        entity_id=deleted_id, entity_type=deleted_type)
    assert len(affected) == 1
    affected = affected[0]
    assert affected['id'] == deleted_id
    assert affected['type'] == deleted_type
    assert len(affected['index']) == 10 - 5

    res, err = translator.query(entity_type=deleted_type)
    assert len(res) == 2

    unaffected = res[0] if res[0]['id'] != deleted_id else res[1]
    assert unaffected['id'] != deleted_id
    assert unaffected['type'] == deleted_type
    assert len(unaffected['index']) == 10
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_delete_entity_with_tenancy(translator):
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=2,
                                      num_updates=5)
    fs = 'fs'
    fsp = 'fsp'
    translator.insert(entities, fiware_service=fs, fiware_servicepath=fsp)

    to_delete = entities[0]
    deleted_type = to_delete['type']
    deleted_id = to_delete['id']

    # No fs nor fsp -> no deletion
    res = translator.delete_entity(deleted_id, entity_type=deleted_type)
    assert res == 0

    # No fsp -> no deletion
    res = translator.delete_entity(deleted_id,
                                   entity_type=deleted_type,
                                   fiware_service=fs)
    assert res == 0

    # Matching fs & fsp -> deletion
    res = translator.delete_entity(deleted_id,
                                   entity_type=deleted_type,
                                   fiware_service=fs,
                                   fiware_servicepath=fsp)
    assert res == 5
    translator.clean(fs)


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_delete_entities_defaults(translator):
    entities = create_random_entities(num_types=3,
                                      num_ids_per_type=2,
                                      num_updates=20)
    translator.insert(entities)

    type_to_delete = entities[0]['type']
    res = translator.delete_entities(type_to_delete)
    assert res == 20 * 2

    remaining, err = translator.query()
    assert len(remaining) == (3 - 1) * 2
    assert all([r['type'] != type_to_delete for r in remaining])
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_delete_entities_customs(translator):
    entities = create_random_entities(num_types=4,
                                      num_ids_per_type=1,
                                      num_updates=4)
    for i, e in enumerate(entities):
        time_index = datetime(2018, 1, 1 + i).isoformat()[:-3]
        e[TIME_INDEX_NAME] = time_index

    translator.insert(entities)

    type_to_delete = entities[-1]['type']
    res = translator.delete_entities(type_to_delete,
                                     from_date=datetime(
                                         2018, 1, 4).isoformat(),
                                     to_date=datetime(2018, 1, 12).isoformat())
    assert res == 3

    remaining, err = translator.query()
    assert sum([len(r['index']) for r in remaining]) == ((4 * 4) - 3)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_delete_entities_with_tenancy(translator):
    fs = 'fs1'
    fsp = 'fsp'
    entities = create_random_entities(num_types=3,
                                      num_ids_per_type=1,
                                      num_updates=10)
    translator.insert(entities, fiware_service=fs, fiware_servicepath=fsp)

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
    translator.clean(fs)
