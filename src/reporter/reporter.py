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
from geocoding import geocoding
from geocoding.factory import get_geo_cache, is_geo_coding_available
from requests import RequestException
from translators.sql_translator import SQLTranslator
from utils.common import iter_entity_attrs, TIME_INDEX_NAME
import json
import logging
import requests
from reporter.timex import select_time_index_value_as_iso, \
    TIME_INDEX_HEADER_NAME
from geocoding.location import normalize_location, LOCATION_ATTR_NAME
from exceptions.exceptions import NGSIUsageError, InvalidParameterValue, InvalidHeaderValue
from wq.ql.notify import InsertAction
from reporter.httputil import fiware_correlator, fiware_s, fiware_sp


def log():
    logger = logging.getLogger(__name__)
    return logger


def is_text(attr_type):
    return SQLTranslator.is_text(attr_type)


def has_value(entity, attr_name):
    attr = entity.get(attr_name, {})
    attr_value = None
    if attr is None:
        attr = {}
    # work around to not drop during validation `modifiedAt` and `observedAt`
    elif isinstance(attr, dict):
        attr_value = attr.get('value', None)
        attr_type = attr.get('type', None)
        if attr_value is None:
            return False

        if is_text(attr_type):
            return True
    else:
        attr_value = attr

    if isinstance(attr_value, str):
        attr_value = attr_value.strip()

    # If type != Text and value == '', make value = null
    return attr_value != '' and attr_value is not None


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
        log().warning("Received notification containing an entity update "
                      "without attributes other than 'type' and 'id'")

    # Attributes should have a value and the modification time
    for attr in attrs:
        if not has_value(payload, attr):
            payload[attr].update({'value': None})
            log().warning(
                'An entity update is missing value '
                'for attribute {}'.format(attr))


def _filter_empty_entities(payload):
    log().debug('Received payload')
    attrs = list(iter_entity_attrs(payload))
    empty = False
    attrs.remove('time_index')
    for j in attrs:
        if 'value' in payload[j]:
            value = payload[j]['value']
        else:
            value = payload[j]
        if isinstance(value, int) and value is not None:
            empty = True
        elif value:
            empty = True
    if empty:
        return payload
    else:
        return None


def _filter_no_type_no_value_entities(payload):
    attrs = list(iter_entity_attrs(payload))
    attrs.remove('time_index')
    for i in attrs:
        attr = payload.get(i, {})
        try:
            attr_value = attr.get('value', None)
            attr_type = attr.get('type', None)
            if not attr_type and not attr_value:
                del payload[i]
        # remove attributes without value or type
        except Exception as e:
            del payload[i]

    return payload


def notify():
    if request.json is None:
        return 'Discarding notification due to lack of request body. ' \
               'Lost in a redirect maybe?', 400

    if 'data' not in request.json:
        return 'Discarding notification due to lack of request body ' \
               'content.', 400

    payload = request.json['data']

    # preprocess and validate each entity update
    for entity in payload:
        # Validate entity update
        error = _validate_payload(entity)
        if error:
            # TODO in this way we return error for even if only one entity
            #  is wrong
            return error, 400
        # Add TIME_INDEX attribute
        custom_index = request.headers.get(TIME_INDEX_HEADER_NAME, None)
        entity[TIME_INDEX_NAME] = \
            select_time_index_value_as_iso(custom_index, entity)
        # Add GEO-DATE if enabled
        if not entity.get(LOCATION_ATTR_NAME, None):
            add_geodata(entity)
        # Always normalize location if there's one
        normalize_location(entity)

    res_entity = []
    e = None
    for entity in payload:
        # Validate entity update
        e = _filter_empty_entities(entity)
        if e is not None:
            # this is not NGSI-LD compliant for `modifiedAt` and similar
            # the logic should be as well changed if we introduce support
            # for `keyValues` formatting
            e_new = _filter_no_type_no_value_entities(e)
            res_entity.append(e_new)
    payload = res_entity
    try:
        InsertAction(fiware_s(), fiware_sp(), fiware_correlator(), payload) \
            .enqueue()
    except Exception as e:
        msg = "Notification not processed or not updated: {}".format(e)
        log().error(msg, exc_info=True)
        error_code = 500
        if e.__class__ == InvalidHeaderValue or \
                e.__class__ == InvalidParameterValue or \
                e.__class__ == NGSIUsageError:
            error_code = 400
        return msg, error_code
    msg = "Notification successfully processed"
    log().info(msg)
    return msg


def add_geodata(entity):
    if is_geo_coding_available():
        cache = get_geo_cache()
        geocoding.add_location(entity, cache=cache)


def config():
    r = {
        "error": "Not Implemented",
        "description": "This API method is not yet implemented."
    }
    return r, 501


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
