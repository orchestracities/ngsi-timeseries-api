from exceptions.exceptions import AmbiguousNGSIIdError, InvalidParameterValue
from flask import request
from reporter.reporter import _validate_query_params
from translators.factory import translator_for
import logging



def query_NTNE(limit=10000,
                 type_=None,  # In Query
                 from_date=None,
                 to_date=None,
                 offset=0):
    """
    See /entities in API Specification
    quantumleap.yml
    """
    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    entities = None
    try:
        with translator_for(fiware_s) as trans:
            entities = trans.query_ids(limit=limit,
                                   entity_type=type_,
                                   from_date=from_date,
                                   to_date=to_date,
                                   offset=offset,
                                   fiware_service=fiware_s,
                                   fiware_servicepath=fiware_sp)
    except NGSIUsageError as e:
        msg = "Bad Request Error: {}".format(e)
        logging.getLogger().error(msg, exc_info=True)
        return msg, 400

    except InvalidParameterValue as e:
        return {
            "error": "{}".format(type(e)),
            "description": str(e)
        }, 422

    except Exception as e:
        msg = "Internal server Error: {}".format(e)
        logging.getLogger().error(msg, exc_info=True)
        return msg, 500

    if entities:
        res = []
        for entity in entities:
            res.append(entity)

        return res

    r = {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
    return r, 404

