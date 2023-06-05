from conftest import QL_URL
from reporter.tests.utils import insert_test_data, delete_test_data, \
    wait_for_insert
import pytest
import requests

entity_type = 'Room'
entity_id = 'Room0'
n_days = 30
services = ['t1', 't2']
entity_type_1 = 'Kitchen'
entity_id_1 = 'Kitchen0'

idPattern = 'R'


def query_url():
    url = "{qlUrl}/entities"
    return url.format(
        qlUrl=QL_URL
    )


@pytest.fixture(scope='module')
def reporter_dataset():
    for service in services:
        insert_test_data(service, [entity_type], n_entities=1, index_size=30,
                         entity_id=entity_id)
        insert_test_data(service, [entity_type_1], n_entities=1, index_size=30,
                         entity_id=entity_id_1)
        wait_for_insert([entity_type, entity_type_1], service, 30)
    yield
    for service in services:
        delete_test_data(service, [entity_type, entity_type_1])


# TODO we removed order comparison given that in
# CRATE4.0 union all and order by don't work correctly with offset
@pytest.mark.parametrize("service", services)
def test_NTNE_defaults(service, reporter_dataset):
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), headers=h)
    assert r.status_code == 200, r.text
    obtained = r.json()
    expected_index = "1970-01-30T00:00:00.000+00:00"
    expected = [
        {
            'entityId': entity_id_1,
            'index': expected_index,
            'entityType': 'Kitchen'
        },
        {
            'entityId': entity_id,
            'index': expected_index,
            'entityType': 'Room'
        }
    ]
    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_not_found(service):
    query_params = {
        'type': 'NotThere'
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


@pytest.mark.parametrize("service", services)
def idpattern_not_found(service):
    query_params = {
        'idPattern': 'NotThere'
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


@pytest.mark.parametrize("service", services)
def test_NTNE_type(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text
    # Assert
    obtained = r.json()
    expected_type = 'Room'
    expected_index = '1970-01-30T00:00:00.000+00:00'
    expected = [{
        'entityId': 'Room0',
        'index': expected_index,
        'entityType': expected_type
    }
    ]
    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_NTNE_idPattern(service, reporter_dataset):
    query_params = {
        'idPattern': idPattern
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text
    # Assert
    obtained = r.json()
    expected_type = 'Room'
    expected_index = '1970-01-30T00:00:00.000+00:00'
    expected = [{
        'entityId': 'Room0',
        'index': expected_index,
        'entityType': expected_type
    }
    ]
    assert obtained == expected

# TODO we removed order comparison given that in
# CRATE4.0 union all and order by don't work correctly with offset


@pytest.mark.parametrize("service", services)
def test_NTNE_fromDate_toDate(service, reporter_dataset):
    # Query
    query_params = {
        'fromDate': "1970-01-06T00:00:00+00:00",
        'toDate': "1980-01-17T00:00:00+00:00",
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    entity_id_1 = 'Kitchen0'
    entity_type_1 = 'Kitchen'
    entity_type = 'Room'
    entity_id = 'Room0'
    expected_index = '1970-01-30T00:00:00.000+00:00'

    # Assert
    obtained = r.json()
    expected = [
        {
            'entityId': entity_id_1,
            'index': expected_index,
            'entityType': entity_type_1
        },
        {
            'entityId': entity_id,
            'index': expected_index,
            'entityType': entity_type
        }]
    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_NTNE_fromDate_toDate_with_quotes(service, reporter_dataset):
    # Query
    query_params = {
        'fromDate': '"1970-01-06T00:00:00+00:00"',
        'toDate': '"1980-01-17T00:00:00+00:00"',
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    entity_id_1 = 'Kitchen0'
    entity_type_1 = 'Kitchen'
    entity_type = 'Room'
    entity_id = 'Room0'
    expected_index = '1970-01-30T00:00:00.000+00:00'
    # Assert
    obtained = r.json()
    expected = [
        {
            'entityId': entity_id_1,
            'index': expected_index,
            'entityType': entity_type_1
        },
        {
            'entityId': entity_id,
            'index': expected_index,
            'entityType': entity_type
        }]
    assert obtained == expected


# TODO we removed order comparison given that in
# CRATE4.0 union all and order by don't work correctly with offset
@pytest.mark.parametrize("service", services)
def test_NTNE_limit(service, reporter_dataset):
    # Query
    query_params = {
        'limit': 1
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    entity_type = 'Kitchen'
    entity_id = 'Kitchen0'
    expected_index = '1970-01-30T00:00:00.000+00:00'

    # Assert
    obtained = r.json()
    expected = [
        {
            'entityId': entity_id,
            'index': expected_index,
            'entityType': entity_type
        }]
    assert obtained == expected


# TODO we removed order comparison given that in
# CRATE4.0 union all and order by don't work correctly with offset
@pytest.mark.parametrize("service", services)
def test_NTNE_offset(service, reporter_dataset):
    # Query
    query_params = {
        'offset': 1
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text

    entity_type = 'Room'
    entity_id = 'Room0'
    expected_index = '1970-01-30T00:00:00.000+00:00'

    # Assert
    obtained = r.json()
    expected = [
        {
            'entityId': entity_id,
            'index': expected_index,
            'entityType': entity_type
        }]
    assert obtained == expected


@pytest.mark.parametrize("service", services)
def test_NTNE_combined(service, reporter_dataset):
    # Query
    query_params = {
        'type': entity_type,
        'offset': 0,
        'fromDate': "1970-01-06T00:00:00+00:00",
        'toDate': "1980-01-20T00:00:00+00:00",
        'limit': 1,
    }
    h = {'Fiware-Service': service}
    r = requests.get(query_url(), params=query_params, headers=h)
    assert r.status_code == 200, r.text
    expected_type = 'Room'
    expected_id = 'Room0'
    expected_index = '1970-01-30T00:00:00.000+00:00'

    # Assert
    obtained = r.json()
    expected = [{
        'entityId': expected_id,
        'index': expected_index,
        'entityType': expected_type
    }]
    assert obtained == expected
