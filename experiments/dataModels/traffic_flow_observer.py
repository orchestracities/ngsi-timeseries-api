"""
Simple script that sends, every SLEEP seconds, a fake instance of the TrafficFlowObserved model (explained in
https://github.com/Fiware/dataModels/blob/master/Transportation/TrafficFlowObserved) to ORION_URL.

Variables can be set as environment variables or directly hardcoded in this script.
"""
from __future__ import print_function
from datetime import datetime, timedelta
import json
import os
import random
import requests
import time

# INPUT
SLEEP = int(os.environ.get('SLEEP', 3))
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')
N_ENTITIES = int(os.environ.get('N_ENTITIES', 3))

# INTERNAL
max_intensity = max(SLEEP, 1)
HEADERS = {
    'Fiware-Service': 'default',
    'Fiware-ServicePath': '/',
}
HEADERS_PUT = HEADERS.copy()
HEADERS_PUT['Content-Type'] = 'application/json'


def get_entities():
    date_from = (datetime.now() - timedelta(seconds=SLEEP)).isoformat()
    date_to = datetime.now().isoformat()

    coords = [
        [51.235170, 4.421283],
        [51.233103, 4.423617],
        [51.257595, 4.432838],
        [51.260580, 4.426038],
        [51.208525, 4.437985],
        [51.210266, 4.425305],
        [51.204714, 4.416675],
        [51.208948, 4.418556],
        [51.217179, 4.341202],
        [51.218305, 4.336690],
    ]

    for n in range(N_ENTITIES):
        entity = {
            "id": 'traffic_flow_observer_{}'.format(n),
            "type": "TrafficFlowObserved",
            "laneId": n % 2,
            "address": {
                "streetAddress": "streetname",
                "addressLocality": "Antwerpen",
                "addressCountry": "BE"
            },
            "location": {
                "type": "LineString",
                "coordinates": coords[n % len(coords)],
            },
            # "dateObserved": "2016-12-07T11:10:00/2016-12-07T11:15:00"  # Not supported by orion
            "dateObservedFrom": date_from,
            "dateObservedTo": date_to,
            "averageHeadwayTime": max_intensity / SLEEP,      # avg time between two consecutive vehicles
            "intensity": max_intensity,     # Total number of vehicles detected
            # "capacity": 0.76,             # Not defined in spec, only in example :/
            "averageVehicleSpeed": 52.6,    # km/h
            "averageVehicleLength": 5.87,   # meters
            "reversedLane": False,
            "laneDirection": "forward",
        }
        yield entity


def get_attrs_to_update(date_from, date_to):
    avg_length = 2 + random.random() * 8
    avg_speed = 10 + random.random() * 90
    intensity = random.randint(0, max_intensity)
    avg_hw_time = 0 if intensity == 0 else float(SLEEP/intensity)

    attrs_to_update = {
        'dateObservedFrom': {'type': 'DateTime', 'value': date_from},
        'dateObservedTo': {'type': 'DateTime', 'value': date_to},
        'intensity': {'type': 'Number', 'value': intensity},
        'averageHeadwayTime': {'type': 'Number', 'value': avg_hw_time},
        'averageVehicleSpeed': {'type': 'Number', 'value': avg_speed},
        'averageVehicleLength': {'type': 'Number', 'value': avg_length},
    }
    return attrs_to_update


if __name__ == '__main__':
    print("Starting {} with options:".format(__file__))
    print("SLEEP: {}".format(SLEEP))
    print("ORION_URL: {}".format(ORION_URL))
    print("N_ENTITIES: {}".format(N_ENTITIES))

    entities = list(get_entities())

    # Insert
    for e in entities:
        time.sleep(SLEEP)
        r = requests.post('{}/v2/entities?options=keyValues'.format(ORION_URL), data=json.dumps(e), headers=HEADERS_PUT)
        if not r.ok:
            if "Already Exists" in r.text:
                print("Already existed: {}".format(e['id']))
                continue
            raise RuntimeError(r.text)
        print("Inserted: {}".format(json.dumps(e)))

    # Update
    date_from = entities[0]['dateObservedTo']

    while True:
        # Random data to update
        date_to = datetime.now().isoformat()

        for e in entities:
            time.sleep(SLEEP)
            attrs_to_update = get_attrs_to_update(date_from, date_to)

            r = requests.patch('{}/v2/entities/{}/attrs'.format(ORION_URL, e['id']),
                               data=json.dumps(attrs_to_update),
                               headers=HEADERS_PUT)
            if not r.ok:
                raise RuntimeError(r.text)
            print("Updated {} with {}".format(e['id'], attrs_to_update))
        date_from = date_to
