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
from datetime import datetime
from flask import request
from geocoding.geocache import GeoCodingCache
from requests import RequestException
from translators.crate import CrateTranslator, CrateTranslatorInstance
from utils.common import iter_entity_attrs
import json
import logging
import os
import requests


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

    # There must be at least one attribute other than id and type
    # (i.e, the changed value)
    attrs = list(iter_entity_attrs(payload))
    if len(attrs) == 0:
        return "Received notification without attributes " \
               "other than 'type' and 'id'"

    # Attributes must have a value and the modification time
    for attr in attrs:
        if 'value' not in payload[attr] or payload[attr]['value'] == '':
            return 'Payload is missing value for attribute {}'.format(attr)


def _get_time_index(payload):
    """
    :param payload:
        The received json data in the notification.

    :return: str
        The notification time index. E.g: '2017-06-29T14:47:50.844'

    The strategy for now is simple. Received notifications are expected to have
    the dateModified field
    (http://docs.orioncontextbroker.apiary.io/#introduction/specification/virtual-attributes)
    If the notification lacks this attribute, we try using the "latest" of the
    modification times of any of the attributes in the notification. If there
    isn't any, the notification received time will be assumed.

    In future, this could be enhanced with customs notifications where user
    specifies which attribute is to be used as "time index".
    """
    if 'dateModified' in payload:
        return payload['dateModified']['value']

    # Orion did not include dateModified at the entity level.
    # Let's use the newest of the changes in any of the attributes.
    dates = set([])
    for attr in iter_entity_attrs(payload):
        if 'dateModified' in payload[attr].get('metadata', {}):
            dates.add(payload[attr]['metadata']['dateModified']['value'])
    if dates:
        return sorted(dates)[-1]

    # Finally, assume current timestamp as dateModified
    return datetime.now().isoformat()


def notify():
    if request.json is None:
        return 'Discarding notification due to lack of request body. ' \
               'Lost in a redirect maybe?', 400

    if 'data' not in request.json:
        return 'Discarding notification due to lack of request body ' \
               'content.', 400

    payload = request.json['data']
    if len(payload) > 1:
        return 'Multiple data elements in notifications not supported yet', 400
    payload = payload[0]

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Received payload: {}'.format(payload))

    # Validate notification
    error = _validate_payload(payload)
    if error:
        return error, 400

    # Add TIME_INDEX attribute
    payload[CrateTranslator.TIME_INDEX_NAME] = _get_time_index(payload)

    # Add GEO-DATE if enabled
    add_geodata(payload)

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
    with CrateTranslatorInstance() as trans:
        trans.insert([payload], fiware_s, fiware_sp)

    msg = 'Notification successfully processed'
    logger.info(msg)
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
              id_pattern=".*",
              attributes=None):
    # Validate Orion
    try:
        r = requests.get(orion_url)
    except RequestException:
        r = None
    if r is None or not r.ok:
        msg = "Orion is not reachable by QuantumLeap at {}. " \
              "Fix your orionUrl.".format(orion_url)
        return msg, 412

    # Prepare subscription
    subscription = {
        "description": "Created by QuantumLeap {}.".format(quantumleap_url),
        "subject": {
            "entities": [
              {
                "idPattern": id_pattern,
              }
            ],
            "condition": {
              "attrs": attributes.split(',') if attributes else []
            }
          },
        "notification": {
            "http": {
              "url": "{}/notify".format(quantumleap_url)
            },
            "attrs": attributes.split(',') if attributes else [],
            "metadata": ["dateCreated", "dateModified"],
        },
        "throttling": 1,
    }
    if entity_type:
        subscription['subject']['entities'][0]['type'] = entity_type

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
        logger = logging.getLogger(__name__)
        logger.debug("subscribing to {} with headers: {} and data: {}")

    return r.text, r.status_code


def _validate_query_params(aggr_period, aggr_method, attr_names, options):
    if aggr_period and not aggr_method:
        r = {
            "error": "Bad parameters use",
            "description": "aggrMethod is compulsory when using aggrPeriod."
        }
        return r, 400
    if options or aggr_period:
        r = {
            "error": "Not implemented option",
            "description": "aggrPeriod and options are not yet implemented."
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
