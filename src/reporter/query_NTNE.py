from exceptions.exceptions import AmbiguousNGSIIdError
from flask import request
from reporter.reporter import _validate_query_params
from translators.crate import CrateTranslatorInstance, CrateTranslator
import logging
from .geo_query_handler import handle_geo_query


def query_NTNE(limit=10000,
                 offset=0):
    """
    See /entities in API Specification
    quantumleap.yml
    """
    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    entities = None
    try:
        with CrateTranslatorInstance() as trans:
            entities = trans.query(limit=limit,
                                   offset=offset,
                                   fiware_service=fiware_s,
                                   fiware_servicepath=fiware_sp)
    except NGSIUsageError as e:
        return {
            "error": "{}".format(type(e)),
            "description": str(e)
        }, 400

    except Exception as e:
        msg = "Internal server Error: {}".format(e)
        logging.getLogger().error(msg, exc_info=True)
        return msg, 500

    if entities:
        ids = []
        for entity in entities:
          ids.append(entity['id'])

        res = {
            'entityId': ids
        }
        return res

    r = {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
    return r, 404


def query_NTNE_value(*args, **kwargs):
    res = query_NTNE(*args, **kwargs)
    if isinstance(res, dict):
        res.pop('entityId', None)
    return res
