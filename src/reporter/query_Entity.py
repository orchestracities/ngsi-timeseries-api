from exceptions.exceptions import NGSIUsageError, InvalidParameterValue
from flask import request
from reporter.reporter import _validate_query_params
from translators.factory import translator_for
import logging
from .geo_query_handler import handle_geo_query


def query_Entity(entity_id,   # In Path
                 type_=None,  # In Query
                 attrs=None):
    """
    See /v2/{entityId} in API Specification
    quantumleap.yml
    """

    if attrs is not None:
        attrs = attrs.split(',')

    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    entities = None
    try:
        with translator_for(fiware_s) as trans:
            entities = trans.query(attr_names=attrs,
                                   entity_type=type_,
                                   entity_id=entity_id,
                                   aggr_method=None,
                                   aggr_period=None,
                                   from_date=None,
                                   to_date=None,
                                   last_n=1,
                                   limit=1,
                                   offset=0,
                                   fiware_service=fiware_s,
                                   fiware_servicepath=fiware_sp,
                                   geo_query=None)
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
            warnings.warn("Not expecting more than one result for a Entity.")

        attributes = []
        ignore = ('type', 'id', 'index')
        attrs = [at for at in sorted(entities[0].keys()) if at not in ignore]
        for at in attrs:
            attributes.append({
                'attrName': at,
                'values': entities[0][at]['values']
            })

        index = entities[0]['index']
        res = {
            'entityId': entity_id,
            'entityType': entities[0]['type'],
            'index': index,
            'attributes': attributes
        }
        logging.getLogger(__name__).info("Query processed successfully")
        return res

    r = {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
    logging.getLogger(__name__).info("No value found for query")
    return r, 404
