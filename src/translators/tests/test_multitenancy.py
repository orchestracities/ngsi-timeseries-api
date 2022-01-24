"""
The translator understands about FIWARE-Service and FIWARE-ServicePath.

The FIWARE-Service is used as a crate db schema. By default, no schema is
specified (Crate uses "doc" schema as default).

The FIWARE-ServicePath will be persisted in the entity tables as an extra
column. This way, the translator will be able filter in the query by
corresponding FIWARE-ServicePath.

The queries using FIWARE-ServicePath will work like...
    select * from entityX where path ~ '/path/here($|/.*)';


To test a single translator use the -k parameter followed by either
timescale or crate.
See https://docs.pytest.org/en/stable/example/parametrize.html
"""
from datetime import datetime
from utils.common import TIME_INDEX_NAME
from conftest import crate_translator, timescale_translator

import pytest


translators = [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
]


def entity(entity_id):
    e = {
        "type": "Room",
        "id": "{}".format(entity_id),
        TIME_INDEX_NAME: datetime.now().isoformat()[:-3],
        "temperature": {
            "value": "{}".format(datetime.now().second),
            "type": "Number",
        },
    }
    return e


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_fiware_tenant(translator):
    # Insert WITH tenant
    e = entity("Room1")
    fs = "tenant"
    fsp = "/"
    translator.insert([e], fiware_service=fs, fiware_servicepath=fsp)

    # Query NO tenant -> No results
    entities, err = translator.query()
    assert len(entities) == 0

    # Query WITH tenant -> Result
    entities, err = translator.query(fiware_service=fs, fiware_servicepath=fsp)
    assert len(entities) == 1
    translator.clean(fs)


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_fiware_tenant_services(translator):
    # Insert in tenant A
    e = entity("X")
    translator.insert([e], fiware_service="A", fiware_servicepath="/")

    # Insert in tenant B
    e = entity("Y")
    translator.insert([e], fiware_service="B", fiware_servicepath="/")

    # Query tenant A
    entities, err = translator.query(
        fiware_service="A", fiware_servicepath="/")
    assert len(entities) == 1
    assert entities[0]['id'] == "X"

    # Query tenant B
    entities, err = translator.query(
        fiware_service="B", fiware_servicepath="/")
    assert len(entities) == 1
    assert entities[0]['id'] == "Y"
    translator.clean("A")
    translator.clean("B")


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_fiware_tenant_servicepath(translator):
    def insert_with_tenant(e, path):
        translator.insert([e], fiware_service="EU", fiware_servicepath=path)

    # Insert entities with different tenant paths
    insert_with_tenant(entity("Rome"), "/eu/italy")
    insert_with_tenant(entity("Berlin"), "/eu/germany")
    insert_with_tenant(entity("Athens"), "/eu/greece/athens")
    insert_with_tenant(entity("Patras"), "/eu/greece/patras")

    entities, err = translator.query(fiware_service="EU",
                                     fiware_servicepath="/eu")
    assert len(entities) == 4

    entities, err = translator.query(fiware_service="EU",
                                     fiware_servicepath="/eu/germany")
    assert len(entities) == 1

    entities, err = translator.query(fiware_service="EU",
                                     fiware_servicepath="/eu/greece")
    assert len(entities) == 2
    assert set([e['id'] for e in entities]) == set(["Athens", "Patras"])

    entities, err = translator.query(fiware_service="EU",
                                     fiware_servicepath="/eu/g")
    assert len(entities) == 0

    entities, err = translator.query(fiware_service="EU",
                                     fiware_servicepath="/eu/greece/athens")
    assert len(entities) == 1
    translator.clean("EU")


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_fiware_empty_tenant_is_no_tenant(translator):
    # Insert with EMPTY tenant
    e = entity("Room1")
    fs = ""
    fsp = ""
    translator.insert([e], fiware_service=fs, fiware_servicepath=fsp)

    # Query WITHOUT tenant -> get results
    entities, err = translator.query()
    assert len(entities) == 1

    # Insert WITHOUT tenant
    e = entity("Room2")
    translator.insert([e])

    # Query with EMPTY tenant -> get results
    entities, err = translator.query()
    assert len(entities) == 2
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_fiware_tenant_reserved_word(translator):
    e = entity("Room1")
    fs = "default"
    fsp = "/"
    translator.insert([e], fiware_service=fs, fiware_servicepath=fsp)

    entities, err = translator.query(fiware_service=fs, fiware_servicepath=fsp)
    assert len(entities) == 1
    translator.clean(fs)
