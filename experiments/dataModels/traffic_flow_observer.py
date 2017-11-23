"""
Simple script that sends, every SLEEP seconds, a fake instance of the
TrafficFlowObserved model (explained in
https://github.com/Fiware/dataModels/tree/master/Transportation/TrafficFlowObserved
) to ORION_URL.

Variables can be set as environment variables or directly hardcoded in this
script.
"""
from __future__ import print_function
from datetime import datetime, timedelta
from experiments.dataModels.utils import insert_entities, COORDS, update_entity
import os
import random
import time


# INPUT
SLEEP = int(os.environ.get('SLEEP', 3))
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')
N_ENTITIES = int(os.environ.get('N_ENTITIES', 3))


def iter_entities():
    date_from = (datetime.now() - timedelta(seconds=SLEEP)).isoformat()
    date_to = datetime.now().isoformat()

    for n in range(N_ENTITIES):
        max_intensity = max(SLEEP, 1)
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
                "coordinates": COORDS[n % len(COORDS)],
            },
            # Not supported by orion
            # "dateObserved": "2016-12-07T11:10:00/2016-12-07T11:15:00"
            "dateObservedFrom": date_from,
            "dateObservedTo": date_to,
            # avg time between two consecutive vehicles
            "averageHeadwayTime": max_intensity / SLEEP,
            "intensity": max_intensity,   # Total number of vehicles detected
            # "capacity": 0.76,           # Not in spec, only in example :/
            "averageVehicleSpeed": 52.6,  # km/h
            "averageVehicleLength": 5.87, # meters
            "reversedLane": False,
            "laneDirection": "forward",
        }
        yield entity


def get_attrs_to_update(date_from, date_to):
    avg_length = 2 + random.random() * 8
    avg_speed = 10 + random.random() * 90
    max_intensity = max(SLEEP, 1)
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

    entities = list(iter_entities())
    insert_entities(entities, SLEEP, ORION_URL)

    date_from = entities[0]['dateObservedTo']
    while True:
        date_to = datetime.now().isoformat()

        for e in entities:
            time.sleep(SLEEP)
            attrs_to_update = get_attrs_to_update(date_from, date_to)
            update_entity(e, attrs_to_update, ORION_URL)

        date_from = date_to
