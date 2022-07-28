from exceptions.exceptions import AmbiguousNGSIIdError, InvalidParameterValue, NGSIUsageError
from flask import request
from reporter.reporter import _validate_query_params
from translators.factory import translator_for
import logging
import warnings


def query_NTNE(limit=10000,
               type_=None,  # In Query
               from_date=None,
               to_date=None,
               offset=0,
               id_pattern=None):
    """
    See /entities in API Specification
    quantumleap.yml
    """
    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', '/')

    entities = None
    try:
        with translator_for(fiware_s) as trans:
            entities = trans.query_ids(limit=limit,
                                       entity_type=type_,
                                       from_date=from_date,
                                       to_date=to_date,
                                       offset=offset,
                                       idPattern=id_pattern,
                                       fiware_service=fiware_s,
                                       fiware_servicepath=fiware_sp,)
    except NGSIUsageError as e:
        msg = "Bad Request Error: {}".format(e)
        logging.getLogger(__name__).error(msg, exc_info=True)
        return msg, 400

    except InvalidParameterValue as e:
        msg = "Bad Request Error: {}".format(e)
        logging.getLogger(__name__).error(msg, exc_info=True)
        return {
            "error": "{}".format(type(e)),
            "description": str(e)
        }, 422

    except Exception as e:
        msg = "Internal server Error: {}".format(e)
        logging.getLogger(__name__).error(msg, exc_info=True)
        return msg, 500

    if entities:
        res = []
        for entity in entities:
            entity['entityId'] = entity['id']
            entity['entityType'] = entity['type']
            entity['index'] = entity['index'][0]
            del entity['id']
            del entity['type']
            res.append(entity)
        logging.warning(
            "usage of id and type rather than entityId and entityType from version 0.9")
        logging.getLogger(__name__).info("Query processed successfully")
        return res

    r = {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
    logging.getLogger(__name__).info("No value found for query")
    return r, 404
