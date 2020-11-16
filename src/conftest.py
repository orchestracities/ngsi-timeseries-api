from crate.client import exceptions
import json
import os
import pymongo as pm
import pytest
import requests

QL_HOST = os.environ.get('QL_HOST', 'quantumleap')
QL_PORT = 8668
QL_URL = "http://{}:{}/v2".format(QL_HOST, QL_PORT)
QL_BASE_URL = "http://{}:{}".format(QL_HOST, QL_PORT)
QL_DEFAULT_DB = os.environ.get('QL_DEFAULT_DB', 'crate')

CRATE_HOST = os.environ.get('CRATE_HOST', 'crate')
CRATE_PORT = 4200

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'timescale')
POSTGRES_HOST = 5432

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = 6379

MONGO_HOST = os.environ.get('MONGO_HOST', 'mongo')
MONGO_PORT = os.environ.get('MONGO_PORT', 27017)

ORION_HOST = os.environ.get('ORION_HOST', 'orion')
ORION_PORT = os.environ.get('ORION_PORT', '1026')
ORION_URL = "http://{}:{}/v2".format(ORION_HOST, ORION_PORT)


def do_clean_mongo():
    db_client = pm.MongoClient(MONGO_HOST, MONGO_PORT)
    for db in db_client.list_database_names():
        db_client.drop_database(db)


@pytest.fixture
def clean_mongo():
    yield
    do_clean_mongo()


def headers(service, service_path, content_type=True):
    h = {}
    if content_type:
        h['Content-Type'] = 'application/json'
    if service:
        h['Fiware-Service'] = service
    if service_path:
        h['Fiware-ServicePath'] = service_path

    return h


# TODO we have fully fledged client library, why not using that?
class OrionClient(object):

    def __init__(self, host, port):
        self.url = 'http://{}:{}'.format(host, port)

    def subscribe(self, subscription, service=None, service_path=None):
        r = requests.post('{}/v2/subscriptions'.format(self.url),
                          data=json.dumps(subscription),
                          headers=headers(service, service_path))
        return r

    def insert(self, entity, service=None, service_path=None):
        r = requests.post('{}/v2/entities'.format(self.url),
                          data=json.dumps(entity),
                          headers=headers(service, service_path))
        return r

    def delete(self, entity_id, service=None, service_path=None):
        r = requests.delete('{}/v2/entities/{}'.format(self.url, entity_id),
                            headers=headers(service, service_path))
        return r

    def delete_subscription(self, subscription_id, service=None,
                            service_path=None):
        r = requests.delete(
            '{}/v2/subscriptions/{}'.format(self.url, subscription_id),
            headers=headers(service, service_path))
        return r


@pytest.fixture
def orion_client():
    oc = OrionClient(ORION_HOST, ORION_PORT)
    yield oc


def do_clean_crate():
    from crate import client
    conn = client.connect(["{}:{}".format(CRATE_HOST, CRATE_PORT)],
                          error_trace=True)
    cursor = conn.cursor()

    try:
        # Clean tables created by user (i.e, not system tables)
        cursor.execute("select table_schema, table_name from "
                       "information_schema.tables "
                       "where table_schema not in ('sys', "
                       "'information_schema', 'pg_catalog')")
        for (ts, tn) in cursor.rows:
            cursor.execute('DROP TABLE IF EXISTS "{}"."{}"'.format(ts, tn))
            try:
                # Just for bc test
                cursor.execute('DROP TABLE IF EXISTS {}.{}'.format(ts, tn))
            except exceptions.ProgrammingError:
                # tests like test_accept_special_chars may break
                pass

    finally:
        cursor.close()


@pytest.fixture()
def clean_crate():
    yield
    do_clean_crate()


@pytest.fixture()
def crate_translator(clean_crate):
    from src.translators.crate import CrateTranslator

    class Translator(CrateTranslator):

        def insert(self, entities,
                   fiware_service=None, fiware_servicepath=None):
            r = CrateTranslator.insert(self, entities,
                                       fiware_service, fiware_servicepath)
            self._refresh(set([e['type'] for e in entities]),
                          fiware_service=fiware_service)
            return r

        def delete_entity(self, entity_id, entity_type=None,
                          fiware_service=None, **kwargs):
            r = CrateTranslator.delete_entity(self, entity_id, entity_type,
                                              fiware_service=fiware_service,
                                              **kwargs)
            try:
                self._refresh([entity_type], fiware_service=fiware_service)
            except exceptions.ProgrammingError:
                pass
            return r

        def delete_entities(self, entity_type=None, fiware_service=None,
                            **kwargs):
            r = CrateTranslator.delete_entities(self, entity_type,
                                                fiware_service=fiware_service,
                                                **kwargs)
            try:
                self._refresh([entity_type], fiware_service=fiware_service)
            except exceptions.ProgrammingError:
                pass
            return r

        def entity_types(self, fiware_service=None, **kwargs):
            r = CrateTranslator.query_entity_types(self, entity_type=None,
                                                   fiware_service=fiware_service,
                                                   **kwargs)
            try:
                self._refresh(r, fiware_service=fiware_service)
            except exceptions.ProgrammingError:
                pass
            return r

        def clean(self, fiware_service=None, **kwargs):
            types = CrateTranslator.query_entity_types(self,
                                                       fiware_service=fiware_service,
                                                       **kwargs)
            if types:
                for t in types:
                    CrateTranslator.drop_table(self, t,
                                               fiware_service=fiware_service,
                                               **kwargs)
                try:
                    self._refresh(types, fiware_service=fiware_service)
                except exceptions.ProgrammingError:
                    pass

    with Translator(host=CRATE_HOST, port=CRATE_PORT) as trans:
        yield trans


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
def sameEntityWithDifferentAttrs():
    """
    Two updates for the same entity with different attributes. The first
    update has temperature and pressure but the second update has only
    temperature.
    """
    entities = [
        {
            'id': 'Room1',
            'type': 'Room',
            'temperature': {
                'value': 24.2,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            },
            'pressure': {
                'value': 720,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            }
        },
        {
            'id': 'Room1',
            'type': 'Room',
            'temperature': {
                'value': 25.2,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:29:30.000Z'
                    }
                }
            }
        }
    ]
    return entities


@pytest.fixture
def diffEntityWithDifferentAttrs():
    """
    Two updates for the same entity with different attributes. The first
    update has temperature and pressure but the second update has only
    temperature.
    """
    entities = [
        {
            'id': 'Room1',
            'type': 'Room',
            'temperature': {
                'value': 24.2,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            },
            'pressure': {
                'value': 720,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            }
        },
        {
            'id': 'Room2',
            'type': 'Room',
            'temperature': {
                'value': 25.2,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            }
        },
        {
            'id': 'Room3',
            'type': 'Room',
            'temperature': {
                'value': 25.2,
                'type': 'Number',
                'metadata': {
                    'dateModified': {
                        'type': 'DateTime',
                        'value': '2019-05-09T15:28:30.000Z'
                    }
                }
            }
        }
    ]
    return entities


@pytest.fixture
def air_quality_observed():
    """
    :return: dict
        The AirQualityObserved model as received within an Orion notification.
    """
    return {
        "id": "CDMX-AmbientObserved-prueba3",
        "type": "AirQualityObserved",
        "address": {
            "type": "StructuredValue",
            "value": {
                "addressCountry": "MX",
                "addressLocality": "Ciudad de México",
                "streetAddress": "Acolman",
                "postOfficeBoxNumber": "22"
            }
        },
        "dateObserved": {
            "type": "DateTime",
            "value": "2016-03-14T17:00:00Z"
        },
        "location": {
            "value": {
                "type": "Point",
                "coordinates": [-98.9109537, 19.6389474]
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


@pytest.fixture
def traffic_flow_observed():
    """
    :return: dict
        The TrafficFlowObserved model as received within an Orion notification.
        Data inserted to orion using traffic_observer script.
    """
    entity = {
        'id': '100',
        'type': 'TrafficFlowObserved',
        'laneDirection': {
            'type': 'Text',
            'value': 'forward',
        },
        'dateObservedFrom': {
            'type': 'Text',
            'value': '2017-11-22T17:17:30.352635Z',
        },
        'averageVehicleLength': {
            'type': 'Number',
            'value': 5.87,
        },
        'averageHeadwayTime': {
            'type': 'Number',
            'value': 1,
        },
        'reversedLane': {
            'type': 'Boolean',
            'value': False,
        },
        'intensity': {
            'type': 'Number',
            'value': 10,
        },
        'laneId': {
            'type': 'Number',
            'value': 0,
        },
        'address': {
            'type': 'StructuredValue',
            'value': {
                'addressLocality': 'Antwerpen',
                'addressCountry': 'BE',
                'streetAddress': 'streetname'
            },
        },
        'dateObservedTo': {
            'type': 'Text',
            'value': '2017-11-22T17:17:40.352652Z'
        },
        'location': {
            'type': 'StructuredValue',
            'value': {
                'type': 'LineString',
                'coordinates': [51.23517, 4.421283]
            }
        },
        'averageVehicleSpeed': {
            'type': 'Number',
            'value': 52.6,
        }
    }
    return entity
