"""
Simple script that sends, every SLEEP seconds, a fake instance of the
AirQualityObserved model (explained in
https://github.com/Fiware/dataModels/tree/master/Environment/AirQualityObserved)
 to ORION_URL.

Variables can be set as environment variables or directly hardcoded in this
script.
"""
from __future__ import print_function
from datetime import datetime
from experiments.dataModels.utils import insert_entities, COORDS, update_entity
import os
import random
import time


# INPUT
SLEEP = int(os.environ.get('SLEEP', 3))
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')
N_ENTITIES = int(os.environ.get('N_ENTITIES', 3))


def iter_entities():
    for n in range(N_ENTITIES):
        entity = {
            "id": 'air_quality_observer_{}'.format(n),
            "type": "AirQualityObserved",
            "address": {
                "streetAddress": "streetname",
                "addressLocality": "Antwerpen",
                "addressCountry": "BE"
            },
            "dateObserved": datetime.now().isoformat(),
            "location": {
                "type": "Point",
                "coordinates": COORDS[n % len(COORDS)],
            },
            "source": "http://random.data.from.quantumleap",
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
            "refPointOfInterest": "28079004-Pza.deEspanya"
        }
        yield entity


def get_attrs_to_update():
    attrs_to_update = {
        'dateObserved': {'type': 'DateTime', 'value': datetime.now().isoformat()},
        "precipitation": {'type': 'Number', 'value': random.randint(0, 200)},
        "relativeHumidity": {'type': 'Number', 'value': random.random()},
        "temperature": {'type': 'Number', 'value': -20 + random.random() * 50},
        "windDirection": {'type': 'Number', 'value':random.random() * 200},
        "windSpeed": {'type': 'Number', 'value': random.random()},
        "airQualityLevel": {
            'type': 'Text',
            'value': random.choice(["poor","moderate", "good"])},
        "airQualityIndex": {'type': 'Number', 'value': random.random() * 100},
        "reliability": {'type': 'Number', 'value': random.random()},
        "CO": {'type': 'Number', 'value': random.random() * 500},
        "NO": {'type': 'Number', 'value': random.random() * 100},
        "NO2": {'type': 'Number', 'value': random.random() * 100},
        "NOx": {'type': 'Number', 'value': random.random() * 150},
        "SO2": {'type': 'Number', 'value': random.random() * 20},
        "CO_Level": {
            'type': 'Text',
            'value': random.choice(["low", "moderate", "high"])},
    }
    return attrs_to_update


if __name__ == '__main__':
    print("Starting {} with options:".format(__file__))
    print("SLEEP: {}".format(SLEEP))
    print("ORION_URL: {}".format(ORION_URL))
    print("N_ENTITIES: {}".format(N_ENTITIES))

    entities = list(iter_entities())
    insert_entities(entities, SLEEP, ORION_URL)

    while True:
        for e in entities:
            time.sleep(SLEEP)
            attrs_to_update = get_attrs_to_update()
            update_entity(e, attrs_to_update, ORION_URL)
