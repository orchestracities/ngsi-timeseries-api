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
import os
import random


# INPUT
SLEEP = int(os.environ.get('SLEEP', 3))
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')
N_ENTITIES = int(os.environ.get('N_ENTITIES', 9))


def create_entity(entity_id):
    from utils import COORDS
    entity = {
        "id": entity_id,
        "type": "AirQualityObserved",
        "address": {
            "streetAddress": "streetname",
            "addressLocality": "Antwerpen",
            "addressCountry": "BE"
        },
        "dateObserved": datetime.now().isoformat(),
        "location": {
            "type": "Point",
            "coordinates": random.choice(COORDS),
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
    return entity


def get_attrs_to_update():
    attrs_to_update = {
        'dateObserved': {
            'type': 'DateTime',
            'value': datetime.now().isoformat()},
        "precipitation": {'type': 'Number', 'value': random.randint(0, 200)},
        "relativeHumidity": {'type': 'Number', 'value': random.random()},
        "temperature": {'type': 'Number', 'value': -20 + random.random() * 50},
        "windDirection": {'type': 'Number', 'value': random.random() * 200},
        "windSpeed": {'type': 'Number', 'value': random.random()},
        "airQualityLevel": {
            'type': 'Text',
            'value': random.choice(["poor", "moderate", "good"])},
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
    from utils import main
    id_prefix = 'air_quality_observer'
    main(
        __file__, SLEEP, ORION_URL, N_ENTITIES,
        id_prefix, create_entity, get_attrs_to_update,)
