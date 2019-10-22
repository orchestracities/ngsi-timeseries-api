from exceptions.exceptions import AmbiguousNGSIIdError
from flask import request
from reporter.reporter import _validate_query_params
from translators.crate import CrateTranslatorInstance, CrateTranslator
import logging
from .geo_query_handler import handle_geo_query


def query_NTNE(entity_id=None,
                 type_=None,
                 attrs=None,
                 aggr_method=None,
                 aggr_period=None,
                 options=None,
                 from_date=None,
                 to_date=None,
                 last_n=None,
                 limit=10000,
                 offset=0,
                 georel=None,
                 geometry=None,
                 coords=None):
    """
    See /entities in API Specification
    quantumleap.yml
    """
    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    entities = None
    try:
        with CrateTranslatorInstance() as trans:
            entities = trans.query(attr_names=attrs,
                                   entity_type=type_,
                                   entity_id=entity_id,
                                   aggr_method=aggr_method,
                                   aggr_period=aggr_period,
                                   from_date=from_date,
                                   to_date=to_date,
                                   last_n=last_n,
                                   limit=limit,
                                   offset=offset,
                                   fiware_service=fiware_s,
                                   fiware_servicepath=fiware_sp,
                                   geo_query=geo_query)
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
