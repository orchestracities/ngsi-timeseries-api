import os
import pytest


QL_HOST = os.environ.get('QL_HOST', "quantumleap")
QL_PORT = 8668
QL_URL = "http://{}:{}".format(QL_HOST, QL_PORT)

CRATE_HOST = os.environ.get('CRATE_HOST', 'crate')
CRATE_PORT = 4200


def do_clean_crate():
    from crate import client
    conn = client.connect(["{}:{}".format(CRATE_HOST, CRATE_PORT)], error_trace=True)
    cursor = conn.cursor()

    try:
        cursor.execute("select table_name from information_schema.tables where table_schema = 'doc'")
        for tn in cursor.rows:
            cursor.execute("DROP TABLE IF EXISTS {}".format(tn[0]))
    finally:
        cursor.close()


@pytest.fixture()
def clean_crate():
    yield
    do_clean_crate()


@pytest.fixture
def entity():
    entity = {
        'id': 'Room1',
        'type': 'Room',
        'temperature': {
            'value': 24.2,
            'type': 'Number',
            'metadata': {}
        },
        'pressure': {
            'value': 720,
            'type': 'Number',
            'metadata': {}
        }
    }
    return entity


@pytest.fixture
def air_quality_observed():
    """
    :return: dict
        The model as received within an Orion notification.
    """
    return {
        "id": "CDMX-AmbientObserved-prueba3",
        "type": "AirQualityObserved",
        "address": {
            "type": "StructuredValue",
            "value": {
                "addressCountry": "MX",
                "addressLocality": "Ciudad de México",
                "streetAddress": "Acolman"
            }
        },
        "dateObserved": {
            "type": "DateTime",
            "value": "2016-03-14T17:00:00-05:00"
        },
        "location": {
            "value": {
                "type": "Point",
                "coordinates": [-99.122984, 19.431768]
            },
            "type": "geo:json"
        },
        "source": {
            "type": "Text",
            "value": "http://www.aire.cdmx.gob.mx/"
        },
        "temperature": {
            "type": "Text",
            "value": "12.2"
        },
        "relativeHumidity": {
            "type": "Text",
            "value": "0.54"
        },
        "measurand": {
            "type": "Array",
            "value": [
                "CO, nr, PPM, Carbon Monoxide",
                "03, 45, PPB, Nitrogen Monoxide",
                "NO2, 69, PPB, Nitrogen Dioxide",
                "SO2, 11, PPB, Sulfur Dioxide",
                "PM10, 139, GQ, Particle Pollution"
            ]
        },
        "CO": {
            "type": "Text",
            "value": "nr"
        },
        "O3": {
            "type": "Text",
            "value": "45"
        },
        "NO2": {
            "type": "Text",
            "value": "69"
        },
        "SO2": {
            "type": "Text",
            "value": "11"
        },
        "PM10": {
            "type": "Text",
            "value": "139"
        }
    }

