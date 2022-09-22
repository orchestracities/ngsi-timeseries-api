import json
import os
import pytest
import requests
from requests import Response
from typing import List, Union

from geocoding.slf.geotypes import SlfBox, SlfLine, SlfPoint, SlfPolygon
from translators.sql_translator import NGSI_DATETIME, NGSI_GEOJSON,\
    NGSI_STRUCTURED_VALUE, NGSI_TEXT, current_timex
from utils.jsondict import maybe_value
from utils.kvt import merge_dicts

from .geo_queries_fixture import query_1t1ena
from .utils import notify_url, insert_entities, gen_entity
from src.utils.tests.tenant import gen_tenant_id


ENTITY_TYPE = 'device'

#
# NOTE. Each test scenario gets a (sort of) unique tenant so that we won't
# have to clean up the DB after each test, which would slow down the whole
# test suite.
#


def entity_name_value_pairs(entity: dict) -> dict:
    """
    Transform an NGSI entity ``e`` into the format::

        {
            entityId: e[id]
            attr1: [ e[attr1][value] ]
            ...
            attrN: [ e[attrN][value] ]
        }
    """
    eid = {'entityId': entity['id']}

    attr_names = {k for k in entity.keys()} - {'id', 'type'}
    attrs = {k: [maybe_value(entity, k, 'value')] for k in attr_names}

    return merge_dicts(eid, attrs)

# TODO: factor out?
# This function and the one below could come in handy when testing a number
# of scenarios where we first insert entities and then query them by ID.


def query_result_name_value_pairs(result: dict) -> dict:
    """
    Extract the result set returned by the ``/v2/entities/{entityId}`` endpoint
    using the same format as that of ``entity_name_value_pairs``.
    """
    eid = {'entityId': maybe_value(result, 'entityId')}

    attrs_array = maybe_value(result, 'attributes')
    attrs_array = attrs_array if attrs_array else []
    attrs = {maybe_value(a, 'attrName'): maybe_value(a, 'values')
             for a in attrs_array}

    return merge_dicts(eid, attrs)


def query_entity_by_id(entity_id: str, service: str = None) -> dict:
    response = query_1t1ena(service, entity_id, {})
    return response.json()


def has_timescale() -> bool:
    return os.getenv('POSTGRES_PORT') is not None
    # see run_tests.timescale.sh

# TODO: zap above method and below skipif after unifying Crate and Timescale
# test suites---i.e. one docker compose, backend selected depending on tenant.
# Keep in mind this test can only run against the timescale backend though.


@pytest.mark.skipif(not has_timescale(),
                    reason='requires timescale backend')
def test_entity_with_all_supported_types():
    service = gen_tenant_id()
    e = gen_entity(entity_id=1,
                   bool_v=True,
                   int_v=123,
                   num_v=321.07,
                   text_v='wada wada',
                   timex=current_timex() + '+00:00',
                   array_v=[123, {}, False],
                   structured_v={'x': 1},
                   geoj_v={'type': 'Point', 'coordinates': [30.02, 10.03],
                           'crs': {'properties': {'name': 'EPSG4326'},
                                   'type': 'name'},
                           'meta': {'srid': 4326}
                           },
                   slf_point_v='41.3763726, 2.186447514',
                   slf_line_v=['1.0, 2.0', '3.0, 4.0'],
                   slf_polygon_v=['0.0, 0.0', '1.0, 0.0', '0.0, 1.0',
                                  '0.0, 0.0'],
                   slf_box_v=['40.63913831188419, -8.653321266174316',
                              '40.63881265804603, -8.653149604797363'])

    insert_entities(e, service=service)

    result_set = query_entity_by_id(e['id'], service)

    actual = query_result_name_value_pairs(result_set)
    expected = entity_name_value_pairs(e)
    assert actual == expected

# TODO: probabilistic testing.
# Since we got this far, it'd be nice to generate a large amount of entities
# at random to get some confidence we can actually store and then get back
# any NGSI entity. See if there's a QuickCheck/QuickSpec/etc. for Python.
