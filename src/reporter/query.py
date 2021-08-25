from exceptions.exceptions import NGSIUsageError, InvalidParameterValue
from flask import request
from reporter.reporter import _validate_query_params, _validate_body
from translators.factory import translator_for
import logging
from .geo_query_handler import handle_geo_query

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

    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    if fiware_sp == '/':
        fiware_sp = None

    res = []
    # Validate entity
    for et in entity:
        entity_type = et["type"]
        entity_id = et["id"]
        eid = entity_id.split()
        entities = None
        try:
            with translator_for(fiware_s) as trans:
                entities = trans.query_last_value(attr_names=attrs,
                                       entity_type=entity_type,
                                       entity_ids=eid,
                                       fiware_service=fiware_s,
                                       fiware_servicepath=fiware_sp)
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
            # Temp workaround to debug test_not_found
            msg = "Something went wrong with QL. Error: {}".format(e)
            logging.getLogger(__name__).error(msg, exc_info=True)
            return msg, 500

        if entities:
            if len(entities) > 1:
                import warnings
                warnings.warn("Not expecting more than one result for a 1T1ENA.")

            logging.getLogger(__name__).info("Query processed successfully")
            entities[0].pop("dateModified")
            res.append(entities[0])
        else:
            r = {
                "error": "Not Found",
                "description": "No records were found for such query."
            }
            logging.getLogger(__name__).info("No value found for query")
            return r, 404
    return res
