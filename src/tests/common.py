import json
import os
import random
import requests
import time


# INPUT VARIABLES
QL_URL = os.environ.get("QL_URL", "http://localhost:8668")
ORION_URL = os.environ.get("ORION_URL", "http://localhost:1026")
ORION_URL_4QL = os.environ.get("ORION_URL_4QL", "http://orion:1026")
QL_URL_4ORION = os.environ.get("QL_URL_4ORION", "http://quantumleap:8668")

# HELPER VARIABLES
ENTITY_TYPE = "IntegrationTestEntity"


class IntegrationTestEntity:
    def __init__(self, e_id, fiware_service=None, fiware_servicepath=None):
        self.FIWARE_SERVICEPATH_KEY = 'Fiware-ServicePath'
        self.id = e_id
        self.type = ENTITY_TYPE

        self.fiware_service = fiware_service
        self.fiware_servicepath = fiware_servicepath

        self.attrs = {
            "int_attr": 120,
            "float_attr": 0.5,
            "text_attr": "blabla",
            "bool_attr": False,
            "obj_attr": {},
        }

    def headers(self):
        h = {}
        if self.fiware_service:
            h['Fiware-Service'] = self.fiware_service
        if self.fiware_servicepath:
            h[self.FIWARE_SERVICEPATH_KEY] = self.fiware_servicepath
        return h

    def payload(self):
        return {'id': self.id, 'type': self.type, **self.attrs}

    def update(self):
        self.attrs['int_attr'] += random.choice((1, -1))
        return {
          "int_attr": {
            "value": self.attrs['int_attr'],
            "type": "Number"
          }
        }

    def __repr__(self):
        return "{}:{}".format(self.type, self.id)


def check_orion_url():
    res = requests.get("{}/version".format(ORION_URL))
    assert res.ok, "{} not accessible. {}".format(ORION_URL, res.text)


def check_ql_url():
    res = requests.get("{}/v2/version".format(QL_URL))
    assert res.ok, "{} not accessible. {}".format(QL_URL, res.text)


def create_entities():
    entities = [
        IntegrationTestEntity("ite1", "Orchestracities", "/ParkingManagement"),
        IntegrationTestEntity("ite2", "Orchestracities", "/ParkingManagement"),
        IntegrationTestEntity("ite3", "Orchestracities", "/WasteManagement"),
        IntegrationTestEntity("ite4", "MyCity", "/WasteManagement"),
        IntegrationTestEntity("ite5", "MyCity", "/"),
        IntegrationTestEntity("ite6"),
    ]
    return entities


def post_orion_subscriptions(entities):
    subscribe_url = "{}/v2/subscribe".format(QL_URL)
    params = {
        'orionUrl': '{}/v2'.format(ORION_URL_4QL),
        'quantumleapUrl': '{}/v2'.format(QL_URL_4ORION),
        'entityType': ENTITY_TYPE,
        'throttling': 0,
    }

    for e in entities:
        r = requests.post(subscribe_url, params=params, headers=e.headers())
        assert r.status_code == 201, "Failed to create Orion Subscription. " \
                                     "{}".format(r.text)


def load_data():
    check_orion_url()
    check_ql_url()

    entities = create_entities()

    # Post Subscriptions in Orion
    post_orion_subscriptions(entities)
    time.sleep(2)

    # Post Entities in Orion
    url = "{}/v2/entities".format(ORION_URL)
    params = {'options': 'keyValues'}
    for e in entities:
        h = {'Content-Type': 'application/json', **e.headers()}
        data = json.dumps(e.payload())
        res = requests.post(url, data=data, params=params, headers=h)
        assert res.ok, res.text
        time.sleep(3)

    # Update Entities in Orion
    for i in range(3):
        for e in entities:
            url = "{}/v2/entities/{}/attrs".format(ORION_URL, e.id)
            h = {'Content-Type': 'application/json', **e.headers()}
            patch = e.update()
            res = requests.patch(url, data=json.dumps(patch), headers=h)
            assert res.ok, res.text
            time.sleep(1)

    return entities


def check_data(entities):
    check_orion_url()
    check_ql_url()

    # Query records in QuantumLeap
    for e in entities:
        # Query specific entity and check values
        url = "{}/v2/entities/{}/attrs/int_attr".format(QL_URL, e.id)
        res = requests.get(url, params={'type': e.type}, headers=e.headers())
        assert res.ok, res.text

        obtained = res.json()
        assert obtained['entityId'] == e.id
        assert obtained['entityId'] == e.id

        index = obtained['index']
        values = obtained['values']
        assert len(index) > 1
        assert index[0] != index[-1]
        assert len(index) == len(values)

        # Now without explicit type to trigger type search in metadata table
        res = requests.get(url, headers=e.headers())
        assert res.ok, res.text

        new_obtained = res.json()
        assert new_obtained == obtained


def unload_data(entities):
    errors = []
    # Cleanup all Subscriptions
    for e in entities:
        h = e.headers()
        r = requests.get("{}/v2/subscriptions".format(ORION_URL), headers=h)
        subs = [s['id'] for s in r.json()] if r.text else []
        for s in subs:
            r = requests.delete("{}/v2/subscriptions/{}".format(ORION_URL, s),
                                headers=h)
            if not r.ok:
                errors.append(r.text)

    # Cleanup Entities
    for e in entities:
        r = requests.delete("{}/v2/entities/{}".format(ORION_URL, e.id),
                            headers=e.headers())
        if not r.ok:
            errors.append(r.text)

    # Cleanup Historical Records
    deleted = set([])
    for e in entities:
        uid = (e.fiware_service, e.type)
        if uid in deleted:
            continue

        # Remove fiware-servicepath so the whole table gets deleted
        h = e.headers()
        if e.FIWARE_SERVICEPATH_KEY in h:
            h.pop(e.FIWARE_SERVICEPATH_KEY)
        url = "{}/v2/types/{}".format(QL_URL, e.type)

        r = requests.delete(url, headers=h)
        if not r.ok:
            errors.append(r.text)
        else:
            deleted.add(uid)

    assert not errors, errors


def check_deleted_data(entities):
    # Check all records removed from QL
    for e in entities:
        url = "{}/v2/entities/{}/attrs/int_attr".format(QL_URL, e.id)
        res = requests.get(url, params={'type': e.type}, headers=e.headers())
        assert not res.ok
        assert res.status_code == 404


if __name__ == '__main__':
    load_data()
