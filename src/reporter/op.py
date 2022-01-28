from exceptions.exceptions import NGSIUsageError, InvalidParameterValue
from flask import request
from reporter.reporter import _validate_query_params
from translators.factory import translator_for
import logging
from .geo_query_handler import handle_geo_query
from reporter.httputil import fiware_s, fiware_sp


def query():
    """
    See /op/query in API Specification
    quantumleap.yml
    """
    if request.json is None:
        return 'Discarding query due to lack of request body. ' \
               'Lost in a redirect maybe?', 400

    if 'entities' not in request.json:
        return 'Discarding query due to lack of request body ' \
               'content.', 400
    # Validate request body
    error = _validate_body(request.json)
    if error:
        return error, 400
    entity = request.json['entities']
    attrs = request.json['attrs']

    res = []
    # Validate entity
    for et in entity:
        entity_type = et["type"]
        entity_id = et["id"]
        eid = entity_id.split()
        entities = None
        try:
            with translator_for(fiware_s()) as trans:
                entities = trans.query_last_value(
                    attr_names=attrs,
                    entity_type=entity_type,
                    entity_ids=eid,
                    fiware_service=fiware_s(),
                    fiware_servicepath=fiware_sp())
        except NGSIUsageError as e:
            msg = "Bad Request Error: {}".format(e)
            logging.getLogger(__name__).error(msg, exc_info=True)
            return {
                "error": "{}".format(type(e)),
                "description": str(e)
            }, 400

        except InvalidParameterValue as e:
            msg = "Bad Request Error: {}".format(e)
            logging.getLogger(__name__).error(msg, exc_info=True)
            return {
                "error": "{}".format(type(e)),
                "description": str(e)
            }, 422

        except Exception as e:
            msg = "Something went wrong with QL. Error: {}".format(e)
            logging.getLogger(__name__).error(msg, exc_info=True)
            return msg, 500

        if entities:
            if len(entities) > 1:
                logging.warning(
                    "Not expecting more than one result for a 1T1ENA.")

            logging.getLogger(__name__).info("Query processed successfully")
            res.append(entities[0])
        else:
            r = {
                "error": "Not Found",
                "description": "No records were found for such query."
            }
            logging.getLogger(__name__).info("No value found for query")
            return r, 404
    return res, 200


def _validate_body(payload):
    """
    :param payload:
        The received json data in the query.
    :return: str | None
        Error message, if any.
    """
    # Not Supported parameters
    if 'expression' in payload:
        return 'expression is Not Supported'
    if 'metadata' in payload:
        return 'metadata is Not Supported'
    for et in payload['entities']:
        # The entity must be uniquely identifiable
        if 'type' not in et:
            return 'Entity type is required'
        if 'id' not in et:
            return 'Entity id is required'
        if 'idPattern' in et:
            return 'idPattern is Not Supported'
