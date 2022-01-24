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

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'timescale')
POSTGRES_PORT = 5432

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

    def update_attr(self, entity_id, attrs, service=None, service_path=None):
        r = requests.patch('{}/v2/entities/{}/attrs'.format(self.url, entity_id),
                           data=json.dumps(attrs),
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
    crate_host = os.environ.get('CRATE_HOST', 'crate')
    crate_port = 4200
    crate_db_username = os.environ.get('CRATE_DB_USER', 'crate')
    crate_db_password = os.environ.get('CRATE_DB_PASS', None)

    from crate import client
    conn = client.connect(["{}:{}".format(crate_host,
                                          crate_port)],
                          error_trace=True,
                          username=crate_db_username,
                          password=crate_db_password)
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
    from src.translators.crate import CrateTranslator, CrateConnectionData
    crate_host = os.environ.get('CRATE_HOST', 'crate')
    crate_port = 4200
    crate_db_username = os.environ.get('CRATE_DB_USER', 'crate')
    crate_db_password = os.environ.get('CRATE_DB_PASS', None)

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
            r = CrateTranslator.query_entity_types(
                self, entity_type=None, fiware_service=fiware_service, **kwargs)
            try:
                self._refresh(r, fiware_service=fiware_service)
            except exceptions.ProgrammingError:
                pass
            return r

        def clean(self, fiware_service=None, **kwargs):
            types = CrateTranslator.query_entity_types(
                self, fiware_service=fiware_service, **kwargs)
            if types:
                for t in types:
                    CrateTranslator.drop_table(self, t,
                                               fiware_service=fiware_service,
                                               **kwargs)
                try:
                    self._refresh(types, fiware_service=fiware_service)
                except exceptions.ProgrammingError:
                    pass

    with Translator(CrateConnectionData(host=crate_host, port=crate_port, db_user=crate_db_username, db_pass=crate_db_password)) as trans:
        yield trans
        trans.dispose_connection()


@pytest.fixture()
def timescale_translator():
    from src.translators.timescale import PostgresTranslator, \
        PostgresConnectionData

    class Translator(PostgresTranslator):

        def insert(self, entities,
                   fiware_service=None, fiware_servicepath=None):
            r = PostgresTranslator.insert(self, entities,
                                          fiware_service, fiware_servicepath)
            return r

        def delete_entity(self, entity_id, entity_type=None,
                          fiware_service=None, **kwargs):
            r = PostgresTranslator.delete_entity(self, entity_id, entity_type,
                                                 fiware_service=fiware_service,
                                                 **kwargs)
            return r

        def delete_entities(self, entity_type=None, fiware_service=None,
                            **kwargs):
            r = PostgresTranslator.delete_entities(
                self, entity_type, fiware_service=fiware_service, **kwargs)
            return r

        def entity_types(self, fiware_service=None, **kwargs):
            r = PostgresTranslator.query_entity_types(
                self, entity_type=None, fiware_service=fiware_service, **kwargs)
            return r

        def clean(self, fiware_service=None, **kwargs):
            types = PostgresTranslator.query_entity_types(
                self, fiware_service=fiware_service, **kwargs)
            if types:
                for t in types:
                    PostgresTranslator.drop_table(
                        self, t, fiware_service=fiware_service, **kwargs)

    with Translator(PostgresConnectionData(host=POSTGRES_HOST,
                                           port=POSTGRES_PORT)) as trans:
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


@pytest.fixture
def ngsi_ld():
    """
    :return: dict
        The NGSI LD model as received within an Orion notification.
    """
    entity = {
        "id": "urn:ngsi-ld:Streetlight:streetlight:guadalajara:4567",
        "type": "Streetlight",
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [-3.164485591715449, 40.62785133667262]
            }
        },
        "areaServed": {
            "type": "Property",
            "value": "Roundabouts city entrance"
        },
        "status": {
            "type": "Property",
            "value": "ok"
        },
        "refStreetlightGroup": {
            "type": "Relationship",
            "object": "urn:ngsi-ld:StreetlightGroup:streetlightgroup:G345"
        },
        "refStreetlightModel": {
            "type": "Relationship",
            "object": "urn:ngsi-ld:StreetlightModel:streetlightmodel:STEEL_Tubular_10m"
        },
        "circuit": {
            "type": "Property",
            "value": "C-456-A467"
        },
        "lanternHeight": {
            "type": "Property",
            "value": 10
        },
        "locationCategory": {
            "type": "Property",
            "value": "centralIsland"
        },
        "powerState": {
            "type": "Property",
            "value": "off"
        },
        "controllingMethod": {
            "type": "Property",
            "value": "individual"
        },
        "dateLastLampChange": {
            "type": "Property",
            "value": {
                "@type": "DateTime",
                "@value": "2016-07-08T08:02:21.753Z"
            }
        },
        "@context": [
            "https://schema.lab.fiware.org/ld/context",
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        ]
    }

    return entity
