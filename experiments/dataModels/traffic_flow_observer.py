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
import os
import random


# INPUT
SLEEP = int(os.environ.get('SLEEP', 3))
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')
N_ENTITIES = int(os.environ.get('N_ENTITIES', 9))


def create_entity(entity_id):
    from utils import COORDS
    pivot = 10
    date_from = (datetime.now() - timedelta(seconds=pivot)).isoformat()
    date_to = datetime.now().isoformat()
    intensity = random.randint(0, pivot)
    avg_hw_time = 0 if intensity == 0 else float(pivot/intensity)
    avg_speed = 1 + random.random() * 250
    avg_length = 2 + random.random() * 8

    entity = {
        "id": entity_id,
        "type": "TrafficFlowObserved",
        "laneId": random.randint(0, 1),
        "address": {
            "streetAddress": "streetname",
            "addressLocality": "Antwerpen",
            "addressCountry": "BE"
        },
        "location": {
            "type": "LineString",
            "coordinates": random.choice(COORDS),
        },
        # Not supported by orion
        # "dateObserved": "2016-12-07T11:10:00/2016-12-07T11:15:00"
        "dateObservedFrom": date_from,
        "dateObservedTo": date_to,
        # avg time between two consecutive vehicles
        "averageHeadwayTime": avg_hw_time,
        "intensity": intensity,        # Total number of vehicles detected
        # "capacity": 0.76,            # Not in spec, only in example :/
        "averageVehicleSpeed": avg_speed,    # km/h
        "averageVehicleLength": avg_length,  # meters
        "reversedLane": False,
        "laneDirection": "forward",
    }
    return entity


def get_attrs_to_update():
    pivot = 10
    date_from = (datetime.now() - timedelta(seconds=pivot)).isoformat()
    date_to = datetime.now().isoformat()
    intensity = random.randint(0, pivot)
    avg_hw_time = 0 if intensity == 0 else float(pivot/intensity)
    avg_speed = 10 + random.random() * 90
    avg_length = 2 + random.random() * 8

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
    from utils import main
    id_prefix = 'traffic_flow_observer'
    main(
        __file__, SLEEP, ORION_URL, N_ENTITIES,
        id_prefix, create_entity, get_attrs_to_update)
