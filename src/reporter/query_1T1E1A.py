from exceptions.exceptions import NGSIUsageError
from flask import request
from reporter.reporter import _validate_query_params
from translators.factory import translator_for
import logging
from .geo_query_handler import handle_geo_query
from utils.jsondict import lookup_string_match


def query_1T1E1A(attr_name,   # In Path
                 entity_id,
                 type_=None,  # In Query
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
    See /entities/{entityId}/attrs/{attrName} in API Specification
    quantumleap.yml
    """
    r, c = _validate_query_params([attr_name], aggr_period, aggr_method,
                                  options=options)
    if c != 200:
        return r, c

    r, c, geo_query = handle_geo_query(georel, geometry, coords)
    if r:
        return r, c

    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    entities = None
    try:
        with translator_for(fiware_s) as trans:
            entities = trans.query(attr_names=[attr_name],
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
        # Temp workaround to debug test_not_found
        msg = "Something went wrong with QL. Error: {}".format(e)
        logging.getLogger().error(msg, exc_info=True)
        return msg, 500

    if entities:
        if len(entities) > 1:
            import warnings
            warnings.warn("Not expecting more than one result for a 1T1E1A.")

        index = [] if aggr_method and not aggr_period else entities[0]['index']
        matched_attr = lookup_string_match(entities[0], attr_name)
        res = {
            'entityId': entities[0]['id'],
            'attrName': attr_name,
            'index': index,
            'values': matched_attr['values'] if matched_attr else []
        }
        return res

    r = {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
    return r, 404


def query_1T1E1A_value(*args, **kwargs):
    res = query_1T1E1A(*args, **kwargs)
    if isinstance(res, dict):
        res.pop('entityId', None)
        res.pop('attrName', None)
    return res
