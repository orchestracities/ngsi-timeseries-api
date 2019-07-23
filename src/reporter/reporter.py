"""
The reporter is the service responsible for handling NGSI notifications,
validating them, and feeding the corresponding updates to the translator.

The reporter needs to know the form of the entity (i.e, name and types of its
attributes). There are two approaches:
    1 - Clients tell reporter which entities they care about and Reporter goes
        find the metadata in Context Broker
    2 - The reporter only consumes the Context Broker notifications and builds
        little by little the whole entity.
        In this case, the notifications must come with some mimimum amount of
        required data (e.g, entity_type, entity_id, a time index and the
        updated value[s]). Ideally, in the first notification the reporter
        would be notified of all the entity attributes so that it can tell the
        translator how to create the complete corresponding table[s] in the
        database.

For now, we have adopted approach 2.

TODO:
- Validate entity and attribute names against valid NGSI names and valid
[Crate names](https://crate.io/docs/crate/reference/en/latest/sql/ddl/basics.html#naming-restrictions)
- Raise warning and act accordingly when receiving entity with equal lowercased
attributes.
- Consider offering an API endpoint to receive just the user's entities of
interest and make QL actually perform the corresponding subscription to orion.
I.e, QL must be told where orion is.
"""
from flask import request
from geocoding.geocache import GeoCodingCache
from requests import RequestException
from translators.crate import CrateTranslator, CrateTranslatorInstance, \
    NGSI_TO_CRATE, NGSI_TEXT, NGSI_DATETIME, NGSI_ISO8601
from translators.factory import translator_for
from utils.common import iter_entity_attrs
import json
import logging
import os
import requests
from reporter.subscription_builder import build_subscription
from reporter.timex import select_time_index_value_as_iso
from geocoding.location import normalize_location


def log():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


def is_text(attr_type):
    return attr_type == NGSI_TEXT or attr_type not in NGSI_TO_CRATE
    # TODO: same logic in two different places!
    # The above kinda reproduces the tests done by the translator, we should
    # factor this logic out and keep it in just one place!


def has_value(entity, attr_name):
    attr = entity.get(attr_name, {})
    if attr is None:
        attr = {}
    attr_value = attr.get('value', None)
    attr_type = attr.get('type', None)

    if attr_value is None:
        return False

    if is_text(attr_type):
        return True

    if isinstance(attr_value, str):
        attr_value = attr_value.strip()

    # If type != Text and value == '', make value = null
    return attr_value != ''


def _validate_payload(payload):
    """
    :param payload:
        The received json data in the notification.
    :return: str | None
        Error message, if any.

    Note that some attributes are actually verified by Connexion framework (
    e.g type and id). We leave the checks as double-checking.
    """
    # The entity must be uniquely identifiable
    if 'type' not in payload:
        return 'Entity type is required in notifications'

    if 'id' not in payload:
        return 'Entity id is required in notifications'

    # There should be at least one attribute other than id and type
    # (i.e, the changed value)
    attrs = list(iter_entity_attrs(payload))
    if len(attrs) == 0:
        log().warning("Received notification containing an entity update without attributes " +
                      "other than 'type' and 'id'")

    # Attributes should have a value and the modification time
    for attr in attrs:
        if not has_value(payload, attr):
            payload[attr].update({'value': None})
            log().warning(
                'An entity update is missing value for attribute {}'.format(attr))


def notify():
    if request.json is None:
        return 'Discarding notification due to lack of request body. ' \
               'Lost in a redirect maybe?', 400

    if 'data' not in request.json:
        return 'Discarding notification due to lack of request body ' \
               'content.', 400

    payload = request.json['data']

    log().info('Received payload: {}'.format(payload))

    # preprocess and validate each entity update
    for entity in payload:
        # Validate entity update
        error = _validate_payload(entity)
        if error:
            return error, 400
    
        # Add TIME_INDEX attribute
        entity[CrateTranslator.TIME_INDEX_NAME] = \
            select_time_index_value_as_iso(request.headers, entity)
    
        # Add GEO-DATE if enabled
        add_geodata(entity)
    
        # Always normalize location if there's one
        normalize_location(entity)

    # Define FIWARE tenant
    fiware_s = request.headers.get('fiware-service', None)
    # It seems orion always sends a 'Fiware-Servicepath' header with value '/'
    # But this is not correctly documented in the API, so in order not to
    # depend on this, QL will not treat servicepath if there's no service
    # specified.
    if fiware_s:
        fiware_sp = request.headers.get('fiware-servicepath', None)
    else:
        fiware_sp = None

    # Send valid entities to translator
    with translator_for(fiware_s) as trans:
        trans.insert(payload, fiware_s, fiware_sp)

    msg = 'Notification successfully processed'
    log().info(msg)
    return msg


def add_geodata(entity):
    # TODO: Move this setting to configuration (See GH issue #10)
    use_geocoding = os.environ.get('USE_GEOCODING', False)
    redis_host = os.environ.get('REDIS_HOST', None)

    # No cache -> no geocoding by default
    if use_geocoding and redis_host:
        redis_port = os.environ.get('REDIS_PORT', 6379)
        cache = GeoCodingCache(redis_host, redis_port)

        from geocoding import geocoding
        geocoding.add_location(entity, cache=cache)


def query_1TNENA():
    r = {
        "error": "Not Implemented",
        "description": "This API method is not yet implemented."
    }
    return r, 501


def query_1TNENA_value():
    r = {
        "error": "Not Implemented",
        "description": "This API method is not yet implemented."
    }
    return r, 501


def query_NTNE1A():
    r = {
        "error": "Not Implemented",
        "description": "This API method is not yet implemented."
    }
    return r, 501


def query_NTNE1A_value():
    r = {
        "error": "Not Implemented",
        "description": "This API method is not yet implemented."
    }
    return r, 501


def query_NTNENA():
    r = {
        "error": "Not Implemented",
        "description": "This API method is not yet implemented."
    }
    return r, 501


def query_NTNENA_value():
    r = {
        "error": "Not Implemented",
        "description": "This API method is not yet implemented."
    }
    return r, 501


def config():
    r = {
        "error": "Not Implemented",
        "description": "This API method is not yet implemented."
    }
    return r, 501


def subscribe(orion_url,
              quantumleap_url,
              entity_type=None,
              entity_id=None,
              id_pattern=None,
              attributes=None,
              observed_attributes=None,
              notified_attributes=None,
              throttling=None,
              time_index_attribute=None):
    # Validate Orion
    try:
        r = requests.get(orion_url)
    except RequestException:
        r = None
    if r is None or not r.ok:
        msg = {
            "error": "Bad Request",
            "description": "Orion is not reachable by QuantumLeap at {}"
            .format(orion_url)
        }
        return msg, 400

    # Prepare subscription
    subscription = build_subscription(
        quantumleap_url,
        entity_type, entity_id, id_pattern,
        attributes, observed_attributes, notified_attributes,
        throttling, time_index_attribute)

    # Send subscription
    endpoint = '{}/subscriptions'.format(orion_url)
    data = json.dumps(subscription)

    headers = {'Content-Type': 'application/json'}
    fiware_s = request.headers.get('fiware-service', None)
    if fiware_s:
        headers['fiware-service'] = fiware_s

        fiware_sp = request.headers.get('fiware-servicepath', None)
        if fiware_sp:
            headers['fiware-servicepath'] = fiware_sp

    r = requests.post(endpoint, data=data, headers=headers)
    if not r.ok:
        log().debug("subscribing to {} with headers: {} and data: {}")

    return r.text, r.status_code


def _validate_query_params(attr_names, aggr_period, aggr_method,
                           aggr_scope=None, options=None):
    if aggr_period and not aggr_method:
        r = {
            "error": "Bad parameters use",
            "description": "aggrMethod is compulsory when using aggrPeriod."
        }
        return r, 400

    if options or aggr_scope not in (None, 'entity'):
        r = {
            "error": "Not implemented option",
            "description": "aggrScope and options are not yet implemented."
        }
        return r, 501

    if aggr_method and not attr_names:
        msg = "Specified aggrMethod = {} but missing attrs parameter."
        r = {
            "error": "Bad parameters use",
            "description": msg.format(aggr_method)
        }
        return r, 400

    return "OK", 200
