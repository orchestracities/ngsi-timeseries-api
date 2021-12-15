from utils.tests.common import *
import os
from conftest import crate_translator as translator


@pytest.fixture
def set_env_vars():
    os.environ['CRATE_DB_USER'] = 'quantumleap'
    os.environ['CRATE_DB_PASS'] = 'a_secret_password'
    yield
    os.environ['CRATE_DB_USER'] = 'crate'
    del os.environ['CRATE_DB_PASS']


def test_auth_is_superuser(translator):
    stmt = "select current_user"
    translator.cursor.execute(stmt)
    res = translator.cursor.fetchall()
    current_user = res[0][0]
    assert current_user == 'crate'


def test_auth_is_not_superuser(set_env_vars, translator):
    stmt = "select current_user"
    translator.cursor.execute(stmt)
    res = translator.cursor.fetchall()
    current_user = res[0][0]
    assert current_user == 'quantumleap'


def test_auth_insert(set_env_vars, translator):
    entities = create_random_entities(1, 2, 3, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0
    translator.clean()


def test_auth_delete_entity_defaults(set_env_vars, translator):
    num_types = 2
    num_ids_per_type = 2
    num_updates = 5

    entities = create_random_entities(num_types, num_ids_per_type, num_updates)
    translator.insert(entities)

    deleted_type = entities[0]['type']
    deleted_id = entities[0]['id']

    total, err = translator.query()
    assert len(total) == num_types * num_ids_per_type

    selected, err = translator.query(entity_type=deleted_type,
                                     entity_id=deleted_id)
    assert len(selected[0]['index']) == num_updates

    n_deleted = translator.delete_entity(deleted_id, entity_type=deleted_type)
    assert n_deleted == num_updates

    remaining, err = translator.query()
    assert len(remaining) == (len(total) - 1)

    survivors, err = translator.query(
        entity_type=deleted_type, entity_id=deleted_id)
    assert len(survivors) == 0
    translator.clean()
