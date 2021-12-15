from exceptions.exceptions import NGSIUsageError, InvalidParameterValue
from conftest import QL_URL
from datetime import datetime
from reporter.tests.utils import insert_test_data, delete_test_data, \
    wait_for_insert
from utils.tests.common import assert_equal_time_index_arrays
from translators.factory import translator_for
import pytest
import requests
import dateutil.parser

entity_type = "Room"
entity_id = "Room1"
n_days = 6
services = ['t1', 't2']


def query_url(etype=entity_type, values=False):
    url = "{qlUrl}/types/{entityType}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        entityType=etype
    )


@pytest.fixture(scope='module')
def reporter_dataset():
    for service in services:
        insert_test_data(service, [entity_type], n_entities=3,
                         entity_id=entity_id, index_size=n_days)
        wait_for_insert([entity_type], service, 3)
    yield
    for service in services:
        delete_test_data(service, [entity_type])


@pytest.mark.parametrize("service", services)
def test_instanceId(service, reporter_dataset):
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), headers=h)
    assert r.status_code == 200, r.text
    entities = None
    with translator_for(service) as trans:
        instanceIds = trans.query_instanceId(entity_id=entity_id,
                                             entity_type=entity_type,
                                             fiware_service=service)

    if instanceIds:
        unique_instanceIds = []

        # traverse for all elements
        for x in instanceIds:
            # check if exists in unique_list or not
            if x not in unique_instanceIds:
                unique_instanceIds.append(x)
        assert len(unique_instanceIds) == len(r.json()['entities'][0]['index'])
