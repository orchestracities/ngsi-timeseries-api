# To test a single translator use the -k parameter followed by either
# timescale or crate.
# See https://docs.pytest.org/en/stable/example/parametrize.html

from utils.tests.common import *

from conftest import crate_auth_translator

import pytest

translators = [
    pytest.lazy_fixture('crate_auth_translator'),
]

# TODO: https://github.com/orchestracities/ngsi-timeseries-api/pull/579#issuecomment-990943040
@pytest.mark.parametrize("translator", [pytest.lazy_fixture('crate_translator')], ids=["crate"])
def test_auth_is_superuser(translator):
    stmt = "select current_user"
    translator.cursor.execute(stmt)
    res = translator.cursor.fetchall()
    current_user = res[0][0]
    assert current_user == 'crate'

@pytest.mark.parametrize("translator", [pytest.lazy_fixture('crate_auth_translator')], ids=["crate-auth"])
def test_auth_is_not_superuser(translator):
    stmt = "select current_user"
    translator.cursor.execute(stmt)
    res = translator.cursor.fetchall()
    current_user = res[0][0]
    assert current_user == 'quantumleap'

@pytest.mark.parametrize("translator", translators, ids=["crate-auth"])
def test_auth_insert(translator):
    entities = create_random_entities(1, 2, 3, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate-auth"])
def test_auth_delete_entity_defaults(translator):
    num_types = 2
    num_ids_per_type = 2
    num_updates = 5

    entities = create_random_entities(num_types, num_ids_per_type, num_updates)
    translator.insert(entities)

    deleted_type = entities[0]['type']
    deleted_id = entities[0]['id']

    total, err = translator.query()
    assert len(total) == num_types * num_ids_per_type

    selected, err = translator.query(entity_type=deleted_type, entity_id=deleted_id)
    assert len(selected[0]['index']) == num_updates

    n_deleted = translator.delete_entity(deleted_id, entity_type=deleted_type)
    assert n_deleted == num_updates

    remaining, err = translator.query()
    assert len(remaining) == (len(total) - 1)

    survivors, err = translator.query(
        entity_type=deleted_type, entity_id=deleted_id)
    assert len(survivors) == 0
    translator.clean()
