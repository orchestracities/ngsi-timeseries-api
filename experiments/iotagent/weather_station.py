"""
Simple script that sends, every SLEEP seconds, a fake instance of the TrafficFlowObserved model (explained in
https://github.com/Fiware/dataModels/blob/master/Transportation/TrafficFlowObserved/doc/spec.md) to ORION_URL.

Variables can be set as environment variables or directly hardcoded in this script.
"""
from __future__ import print_function
import json
import os
import random
import requests
import socket
import time

# INPUT
SLEEP = os.environ.get('SLEEP', 10)
ORION_HOST = os.environ.get('ORION_HOST', '0.0.0.0')
ORION_PORT = os.environ.get('ORION_PORT', '1026')
ORION_URL = 'http://{}:{}'.format(ORION_HOST, ORION_PORT)

# INTERNAL
HEADERS = {
    'Fiware-Service': 'default',
    'Fiware-ServicePath': '/',
}
HEADERS_PUT = HEADERS.copy()
HEADERS_PUT['Content-Type'] = 'application/json'


def get_entity():
    entity_id = "station{}".format(socket.gethostname())
    entity = {
        "id": entity_id,
        "type": "WeatherStation",
    }
    entity.update(get_attrs_to_update())
    return entity


def get_attrs_to_update():
    temperature = random.random() * 50
    pressure = 800 + random.random() * 400
    humidity = random.random() * 100
    attrs_to_update = {
        'temperature': {'type': 'Number', 'value': temperature},
        'pressure': {'type': 'Number', 'value': pressure},
        'humidity': {'type': 'Number', 'value': humidity},
    }
    return attrs_to_update


if __name__ == '__main__':
    print("Starting {} with options:".format(__file__))
    print("SLEEP: {}".format(SLEEP))
    print("ORION_URL: {}".format(ORION_URL))

    entity = get_entity()
    entity_id = entity['id']

    # Insert
    r = requests.post('{}/v2/entities?options=keyValues'.format(ORION_URL), data=json.dumps(entity), headers=HEADERS_PUT)
    if not r.ok:
        raise RuntimeError(r.text)
    print("Inserted: {}".format(entity))

    try:
        while True:
            time.sleep(SLEEP)

            # Update
            attrs_to_update = get_attrs_to_update()
            r = requests.patch('{}/v2/entities/{}/attrs'.format(ORION_URL, entity_id), data=json.dumps(attrs_to_update),
                               headers=HEADERS_PUT)
            if not r.ok:
                raise RuntimeError(r.text)
            print("Updated: {}".format(attrs_to_update))

    finally:
        # Delete
        r = requests.delete('{}/v2/entities/{}'.format(ORION_URL, entity_id), headers=HEADERS)
