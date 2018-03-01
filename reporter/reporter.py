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
from translators.crate import CrateTranslator, CrateTranslatorInstance
from utils.common import iter_entity_attrs
import logging
import os
import warnings


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

        if 'dateModified' not in payload[attr]['metadata']:
            msg = "Attribute '{}' did not include a dateModified. " \
                  "Assuming notification arrival time."
            warnings.warn(msg.format(attr))


def _get_time_index(payload):
    """
    :param payload:
        The received json data in the notification.

    :return: str
        The notification time index. E.g: '2017-06-29T14:47:50.844'

    The strategy for now is simple. Received notifications are expected to have
    the dateModified field
    (http://docs.orioncontextbroker.apiary.io/#introduction/specification/virtual-attributes)
    If the notification lacks this attribute, the received time will be assumed.

    In future, this could be enhanced with customs notifications where user
    specifies which attribute is to be used as "time index".
    """
    if 'dateModified' in payload:
        return payload['dateModified']

    for attr in iter_entity_attrs(payload):
        if 'dateModified' in payload[attr].get('metadata', {}):
            return payload[attr]['metadata']['dateModified']['value']

    # Assume current timestamp as dateModified
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

    # Send valid entities to translator
    with CrateTranslatorInstance() as trans:
        trans.insert([payload])

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


def query_1TNE1A():
    raise NotImplementedError


def query_1TNE1A_value():
    raise NotImplementedError


def query_1TNENA():
    raise NotImplementedError


def query_1TNENA_value():
    raise NotImplementedError


def query_NTNE1A():
    raise NotImplementedError


def query_NTNE1A_value():
    raise NotImplementedError


def query_NTNENA():
    raise NotImplementedError


def query_NTNENA_value():
    raise NotImplementedError


def config():
    raise NotImplementedError
