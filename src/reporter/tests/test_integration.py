from conftest import QL_URL, ORION_URL, entity, clean_mongo, clean_crate
import json
import time
import requests


def test_integration(entity, clean_mongo, clean_crate):
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
    time.sleep(2)

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
        time.sleep(2)

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
    assert len(data['index']) == 4
    assert len(data['attributes']) == 2
    assert data['attributes'][0]['values'] == [720.0, 721.0, 722.0, 723.0]
    assert data['attributes'][1]['values'] == [24.2, 25.2, 26.2, 27.2]
