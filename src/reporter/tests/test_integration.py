from conftest import QL_URL, ORION_URL, entity, clean_mongo
import json
import time
import requests
from .utils import delete_entity_type

def test_integration(entity, clean_mongo):
    # Subscribe QL to Orion
    params = {
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
    }
    r = requests.post("{}/subscribe".format(QL_URL), params=params)
    assert r.status_code == 201

    # Insert values in Orion
    h = {'Content-Type': 'application/json'}
    data = json.dumps(entity)
    r = requests.post('{}/entities'.format(ORION_URL), data=data, headers=h)
    assert r.ok
    time.sleep(1)

    # Update values in Orion
    for i in range(1, 4):
        attrs = {
            'temperature': {
                'value': entity['temperature']['value'] + i,
                'type': 'Number',
            },
            'pressure': {
                'value': entity['pressure']['value'] + i,
                'type': 'Number',
            },
        }
        endpoint = '{}/entities/{}/attrs'.format(ORION_URL, entity['id'])
        r = requests.patch(endpoint, data=json.dumps(attrs), headers=h)
        assert r.ok
        time.sleep(1)

    # Query in Quantumleap
    query_params = {
        'type': entity['type'],
    }
    query_url = "{qlUrl}/entities/{entityId}".format(
        qlUrl=QL_URL,
        entityId=entity['id'],
    )
    r = requests.get(query_url, params=query_params)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data['index']) > 1
    assert len(data['attributes']) == 2

    # Note some notifications may have been lost
    pressures = data['attributes'][0]['values']
    assert set(pressures).issubset(set([720.0, 721.0, 722.0, 723.0]))
    temperatures = data['attributes'][1]['values']
    assert set(temperatures).issubset(set([24.2, 25.2, 26.2, 27.2]))
    delete_entity_type(None, entity['type'])


def test_integration_custom_index(entity, clean_mongo):
    # Subscribe QL to Orion
    params = {
        'orionUrl': ORION_URL,
        'quantumleapUrl': QL_URL,
        'timeIndexAttribute': 'myCustomIndex'
    }
    r = requests.post("{}/subscribe".format(QL_URL), params=params)
    assert r.status_code == 201

    # Insert values in Orion
    entity['myCustomIndex'] = {
        'value': '2019-08-22T18:22:00',
        'type': 'DateTime',
        'metadata': {}
    }
    entity.pop('temperature')
    entity.pop('pressure')

    data = json.dumps(entity)
    h = {'Content-Type': 'application/json'}
    r = requests.post('{}/entities'.format(ORION_URL), data=data, headers=h)
    assert r.ok
    time.sleep(1)

    # Update values in Orion
    for i in range(1, 4):
        attrs = {
            'myCustomIndex': {
                'value': '2019-08-22T18:22:0{}'.format(i),
                'type': 'DateTime',
            },
        }
        endpoint = '{}/entities/{}/attrs'.format(ORION_URL, entity['id'])
        r = requests.patch(endpoint, data=json.dumps(attrs), headers=h)
        assert r.ok
        time.sleep(1)

    # Query in Quantumleap
    query_params = {
        'type': entity['type'],
    }
    query_url = "{qlUrl}/entities/{entityId}".format(
        qlUrl=QL_URL,
        entityId=entity['id'],
    )
    r = requests.get(query_url, params=query_params)
    assert r.status_code == 200, r.text

    data = r.json()
    # Note some notifications may have been lost
    assert data['attributes'][0]['values'] == data['index']
    assert len(data['index']) > 1
    delete_entity_type(None, entity['type'])
