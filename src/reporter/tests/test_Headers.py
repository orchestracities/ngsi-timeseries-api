from datetime import datetime
from conftest import QL_URL
from utils.common import assert_equal_time_index_arrays
import copy
import json
import pytest
import requests
import time
notify_url = "{}/notify".format(QL_URL)

HEADERS_VALID = {'Content-Type': 'application/json', 'fiware-Service': 'test', 'fiware-ServicePath': '/t1'}
HEADERS_INVALID = {'Content-Type': 'application/json', 'fiwareService': 'test', 'fiwareServicePath': '/t1'}

def test_for_valid_headers(notification):
    notification['data'][0] = {
        'id': 'Room0',
        'type': 'Room',
        'temperature': {'type': 'Number', 'value': '100', 'metadata': {'dateModified': {'type': 'DateTime','value': '1980-01-30T00:00:00.000+00:00'}}},
        'pressure': {'type': 'Number', 'value': '10', 'metadata': {'dateModified': {'type': 'DateTime','value': '1980-01-30T00:00:00.000+00:00'}}},
    }

    res_post = requests.post('{}'.format(notify_url), data=json.dumps(notification),
                      headers=HEADERS_VALID)
    time.sleep(1)
    assert res_post.status_code == 200
    assert res_post.json() == 'Notification successfully processed'

    get_url = "{}/entities/Room0".format(QL_URL)
    res_get = requests.get(get_url, headers=HEADERS_VALID)

    assert res_get.status_code == 200

    exp_values = {
        "attributes": [{'attrName': 'pressure', 'values': [10.0]}, {'attrName': 'temperature', 'values': [100.0]}],
        "entityId": 'Room0',
        "index": [
            '1980-01-30T00:00:00.000+00:00'
        ]
    }
    assert res_get.json() == exp_values

def test_for_invalid_headers(notification):
    notification['data'][0] = {
        'id': 'Room0',
        'type': 'Room',
        'temperature': {'type': 'Number', 'value': '200', 'metadata': {}},
        'pressure': {'type': 'Number', 'value': '20', 'metadata': {}},
    }

    res_post = requests.post('{}'.format(notify_url), data=json.dumps(notification),
                      headers=HEADERS_VALID)

    assert res_post.status_code == 200
    assert res_post.json() == 'Notification successfully processed'

    get_url = "{}/entities/Room0".format(QL_URL)
    res_get = requests.get(get_url, headers=HEADERS_INVALID)

    assert res_get.status_code == 404

    exp_result = {'description': 'No records were found for such query.', 'error': 'Not Found'}
    assert res_get.json() == exp_result
