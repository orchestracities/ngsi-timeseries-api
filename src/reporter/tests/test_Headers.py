from conftest import QL_URL
from reporter.tests.utils import delete_entity_type, wait_for_insert
import json
import requests


notify_url = "{}/notify".format(QL_URL)

SERVICE = 'test'
ENTITY_TYPE = 'Room'
HEADERS_VALID = {'Content-Type': 'application/json',
                 'fiware-Service': SERVICE, 'fiware-ServicePath': '/t1'}
HEADERS_INVALID = {'Content-Type': 'application/json',
                   'fiwareService': SERVICE, 'fiwareServicePath': '/t1'}


def insert_data(notification: dict, headers: dict):
    res_post = requests.post(
        '{}'.format(notify_url),
        data=json.dumps(notification),
        headers=headers)

    wait_for_insert([ENTITY_TYPE], SERVICE, len(notification['data']))

    assert res_post.status_code == 200
    assert res_post.json().startswith('Notification successfully processed')


def test_for_valid_headers(notification):
    notification['data'][0] = {
        'id': 'Room0',
        'type': ENTITY_TYPE,
        'temperature': {
            'type': 'Number',
            'value': '100',
            'metadata': {
                'dateModified': {
                    'type': 'DateTime',
                    'value': '1980-01-30T00:00:00.000+00:00'}}},
        'pressure': {
            'type': 'Number',
                    'value': '10',
                    'metadata': {
                        'dateModified': {
                            'type': 'DateTime',
                            'value': '1980-01-30T00:00:00.000+00:00'}}},
    }

    insert_data(notification, HEADERS_VALID)

    get_url = "{}/entities/Room0".format(QL_URL)
    res_get = requests.get(get_url, headers=HEADERS_VALID)

    assert res_get.status_code == 200

    exp_values = {"attributes": [{'attrName': 'pressure',
                                  'values': [10.0]},
                                 {'attrName': 'temperature',
                                  'values': [100.0]}],
                  "entityId": 'Room0',
                  "entityType": 'Room',
                  "index": ['1980-01-30T00:00:00.000+00:00']}
    assert res_get.json() == exp_values
    delete_entity_type('test', 'Room')


def test_for_invalid_headers(notification):
    notification['data'][0] = {
        'id': 'Room0',
        'type': ENTITY_TYPE,
        'temperature': {'type': 'Number', 'value': '200', 'metadata': {}},
        'pressure': {'type': 'Number', 'value': '20', 'metadata': {}},
    }

    insert_data(notification, HEADERS_VALID)

    get_url = "{}/entities/Room0".format(QL_URL)
    res_get = requests.get(get_url, headers=HEADERS_INVALID)

    assert res_get.status_code == 404

    exp_result = {
        'description': 'No records were found for such query.',
        'error': 'Not Found'}
    assert res_get.json() == exp_result
