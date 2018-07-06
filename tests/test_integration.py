import json
import logging
import os
import requests
import time

logger = logging.getLogger(__name__)

# INPUT VARIABLES
QL_URL = os.environ.get("QL_URL", "http://localhost:8668")
ORION_URL = os.environ.get("ORION_URL", "http://localhost:1026")
ORION_URL_4QL = os.environ.get("ORION_URL_4QL", "http://orion:1026")
QL_URL_4ORION = os.environ.get("QL_URL_4ORION", "http://quantumleap:8668")

HEADERS_PUT = {'Content-Type': 'application/json'}


def get_entity(entity_type, entity_id):
    return {
        "id": entity_id,
        "type": entity_type,
        "address": {
            "streetAddress": "IJzerlaan",
            "postOfficeBoxNumber": "18",
            "addressLocality": "Antwerpen",
            "addressCountry": "BE"
        },
        "dateObserved": "2017-11-03T12:37:23.734827",
        "source": "http://testing.data.from.smartsdk",
        "precipitation": 0,
        "relativeHumidity": 0.54,
        "temperature": 12.2,
        "windDirection": 186,
        "windSpeed": 0.64,
        "airQualityLevel": "moderate",
        "airQualityIndex": 65,
        "reliability": 0.7,
        "CO": 500,
        "NO": 45,
        "NO2": 69,
        "NOx": 139,
        "SO2": 11,
        "CO_Level": "moderate",
        "refPointOfInterest": "null"
    }


def create_orion_subscription(orion_url, ql_url, entity_type):
    # Some overhead due to
    # https://github.com/telefonicaid/fiware-orion/issues/3237
    old_sub_ids = set([])
    subs = requests.get("{}/v2/subscriptions".format(orion_url))
    if subs.text:
        old_sub_ids.update(set([s['id'] for s in subs.json()]))

    # Create ORION Subscription
    subscribe_url = "{}/v2/subscribe".format(ql_url)
    params = {
        'orionUrl': '{}/v2'.format(ORION_URL_4QL),
        'quantumleapUrl': '{}/v2'.format(QL_URL_4ORION),
        'entityType': entity_type,
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 201, "Failed to create Orion Subscription. " \
                                 "{}".format(r.text)

    # Get Sub id to delete it later
    subs = requests.get("{}/v2/subscriptions".format(ORION_URL))
    new_sub_ids = set([s['id'] for s in subs.json()])

    created_ids = new_sub_ids.difference(old_sub_ids)
    if len(created_ids) == 1:
        return created_ids.pop()

    if len(created_ids) > 1:
        # A sub was created in the meantime. Get the correct one.
        for i in created_ids:
            s = requests.get("{}/v2/subscriptions/{}".format(ORION_URL, i))
            if s.ok and 'TestIntegrationEntity' in s.text:
                return i
    assert False


def test_integration():
    """
    Sanity Check for a complete deployment of QuantumLeap.
    Make sure to set/edit the INPUT VARIABLES.
    """
    # Validate QL_URL
    res = requests.get("{}/v2/version".format(QL_URL))
    assert res.ok, "{} not accessible. {}".format(QL_URL, res.text)

    # Validate ORION_URL
    res = requests.get("{}/version".format(ORION_URL))
    assert res.ok, "{} not accessible. {}".format(ORION_URL, res.text)

    # Prepare entity
    entity_id = 'test_integration_entity_001'
    entity_type = 'TestIntegrationEntity'
    entity = get_entity(entity_type, entity_id)

    # Create Subscription
    sub_id = create_orion_subscription(ORION_URL, QL_URL, entity_type)
    time.sleep(1)

    try:
        # Insert Data in ORION
        data = json.dumps(entity)
        url = "{}/v2/entities".format(ORION_URL)
        params = {'options': 'keyValues'}
        res = requests.post(url, data=data, params=params, headers=HEADERS_PUT)
        assert res.ok

        time.sleep(2)

        # Update values in Orion
        patch = {
          "precipitation": {
            "value": 100,
            "type": "Number"
          }
        }
        url = "{}/v2/entities/{}/attrs".format(ORION_URL, entity_id)
        res = requests.patch(url, data=json.dumps(patch), headers=HEADERS_PUT)
        assert res.ok

        time.sleep(2)

        # Query records in QuantumLeap
        url = "{}/v2/entities/{}/attrs/precipitation".format(QL_URL, entity_id)
        res = requests.get(url, params={'type': entity_type})
        assert res.ok
        assert len(res.json()['data']['index']) > 1

    finally:
        # Cleanup Subscription
        r = requests.delete("{}/v2/subscriptions/{}".format(ORION_URL, sub_id))
        assert r.ok

        # Cleanup Entity
        r = requests.delete("{}/v2/entities/{}".format(ORION_URL, entity_id))
        assert r.ok

        # Cleanup Historical Records
        r = requests.delete("{}/v2/types/{}".format(QL_URL, entity_type))
        assert r.ok
