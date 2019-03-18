import json
import os
import requests
import time


# INPUT VARIABLES
QL_URL = os.environ.get("QL_URL", "http://localhost:8668")
ORION_URL = os.environ.get("ORION_URL", "http://localhost:1026")
ORION_URL_4QL = os.environ.get("ORION_URL_4QL", "http://orion:1026")
QL_URL_4ORION = os.environ.get("QL_URL_4ORION", "http://quantumleap:8668")

# HELPER VARIABLES
HEADERS_PUT = {'Content-Type': 'application/json'}
ENTITY_ID = "test_integration_entity_001"
ENTITY_TYPE = "TestIntegrationEntity"


def check_orion_url():
    res = requests.get("{}/version".format(ORION_URL))
    assert res.ok, "{} not accessible. {}".format(ORION_URL, res.text)


def check_ql_url():
    res = requests.get("{}/v2/version".format(QL_URL))
    assert res.ok, "{} not accessible. {}".format(QL_URL, res.text)


def create_orion_subscription():
    # Create ORION Subscription
    subscribe_url = "{}/v2/subscribe".format(QL_URL)
    params = {
        'orionUrl': '{}/v2'.format(ORION_URL_4QL),
        'quantumleapUrl': '{}/v2'.format(QL_URL_4ORION),
        'entityType': ENTITY_TYPE,
    }
    r = requests.post(subscribe_url, params=params)
    assert r.status_code == 201, "Failed to create Orion Subscription. " \
                                 "{}".format(r.text)


def load_data():
    check_orion_url()
    check_ql_url()

    create_orion_subscription()
    time.sleep(5)

    # Create Entities
    entity = {
        "id": ENTITY_ID,
        "type": ENTITY_TYPE,
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

    # Insert Entities in ORION
    data = json.dumps(entity)
    url = "{}/v2/entities".format(ORION_URL)
    params = {'options': 'keyValues'}
    res = requests.post(url, data=data, params=params, headers=HEADERS_PUT)
    assert res.ok, res.text
    time.sleep(5)

    # Update Entities in Orion
    patch = {
      "precipitation": {
        "value": 100,
        "type": "Number"
      }
    }
    url = "{}/v2/entities/{}/attrs".format(ORION_URL, ENTITY_ID)
    res = requests.patch(url, data=json.dumps(patch), headers=HEADERS_PUT)
    assert res.ok, res.text

    time.sleep(5)


def check_data():
    # Query records in QuantumLeap
    url = "{}/v2/entities/{}/attrs/precipitation".format(QL_URL, ENTITY_ID)
    res = requests.get(url, params={'type': ENTITY_TYPE})
    assert res.ok, res.text

    obtained = res.json()
    index = obtained['data']['index']
    assert len(index) > 1
    assert index[0] != index[-1]


def unload_data():
    # Cleanup Subscription
    r = requests.get("{}/v2/subscriptions".format(ORION_URL))
    subs = [s['id'] for s in r.json()] if r.text else []
    for s in subs:
        r = requests.delete("{}/v2/subscriptions/{}".format(ORION_URL, s))
        assert r.ok, r.text

    # Cleanup Entity
    r = requests.delete("{}/v2/entities/{}".format(ORION_URL, ENTITY_ID))
    assert r.ok, r.text

    # Cleanup Historical Records
    r = requests.delete("{}/v2/types/{}".format(QL_URL, ENTITY_TYPE))
    assert r.ok, r.text


if __name__ == '__main__':
    load_data()
