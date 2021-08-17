# To test a single translator use the -k parameter followed by either
# timescale or crate.
# See https://docs.pytest.org/en/stable/example/parametrize.html

from exceptions.exceptions import AmbiguousNGSIIdError
from translators.base_translator import BaseTranslator
from translators.sql_translator import NGSI_TEXT, METADATA_TABLE_NAME
from utils.common import *
from utils.tests.common import *
from datetime import datetime, timezone
from conftest import crate_translator, timescale_translator, entity
import pytest
import os


@pytest.fixture()
def enable_caching():
    os.environ["CACHE_QUERIES"] = "True"
    yield
    os.environ["CACHE_QUERIES"] = "False"


def check_cache_operations(translator, fiware_service, entity_table):
    db_cache_name = translator.get_db_cache_name()
    assert translator._is_query_in_cache(db_cache_name, METADATA_TABLE_NAME)
    assert translator._is_query_in_cache(db_cache_name, entity_table)
    assert translator._is_query_in_cache(fiware_service.lower(), "tableNames")
    translator._remove_from_cache(fiware_service.lower(), "tableNames")
    assert not translator._is_query_in_cache(
        fiware_service.lower(), "tableNames")


@pytest.mark.parametrize("translator", [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
], ids=["crate", "timescale"])
def test_cache_insert_no_tenant(enable_caching, translator):
    entities = create_random_entities(1, 2, 3, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0
    entity_table = translator._get_et_table_names(None)[0]
    # When there is no service, they key used is ""
    check_cache_operations(translator, "", entity_table)
    translator.clean()


@pytest.mark.parametrize("translator", [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
], ids=["crate", "timescale"])
def test_cache_insert_with_tenant(enable_caching, translator):
    fiware_service = "Test"
    entities = create_random_entities(1, 2, 3, use_time=True, use_geo=True)
    result = translator.insert(entities, fiware_service=fiware_service,
                               fiware_servicepath="/")
    assert result.rowcount > 0
    entity_table = translator._get_et_table_names(fiware_service)[0]
    check_cache_operations(translator, fiware_service, entity_table)
    translator.clean()


@pytest.mark.parametrize("translator", [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
], ids=["crate", "timescale"])
def test_cache_failure(docker_services, enable_caching, translator):
    fiware_service = "Test"
    docker_services._docker_compose.execute('stop', 'redis')
    entities = create_random_entities(1, 2, 3, use_time=True, use_geo=True)
    result = translator.insert(entities, fiware_service=fiware_service,
                               fiware_servicepath="/")
    assert result.rowcount > 0
    entity_table = translator._get_et_table_names(fiware_service)[0]
    db_cache_name = translator.get_db_cache_name()
    assert translator._is_query_in_cache(
        db_cache_name, METADATA_TABLE_NAME) is False
    assert translator._is_query_in_cache(db_cache_name, entity_table) is False
    docker_services.start('redis')
    translator.clean()
