from exceptions.exceptions import NGSIUsageError, InvalidParameterValue
from utils.jsondict import lookup_string_match
from flask import request
from reporter.reporter import _validate_query_params
import logging
import warnings
from .geo_query_handler import handle_geo_query
import dateutil.parser
from datetime import datetime, timezone
from translators.factory import translator_for


def query_NTNENA(id_=None,  # In Query
                 attrs=None,
                 type_=None,
                 aggr_method=None,
                 aggr_period=None,
                 aggr_scope=None,
                 options=None,
                 from_date=None,
                 to_date=None,
                 last_n=None,
                 limit=10000,
                 offset=0,
                 georel=None,
                 geometry=None,
                 coords=None,
                 id_pattern=None):
    """
    See /v2/attrs in API Specification
    quantumleap.yml
    """
    r, c = _validate_query_params(attrs, aggr_period, aggr_method, aggr_scope,
                                  options)
    if c != 200:
        return r, c

    r, c, geo_query = handle_geo_query(georel, geometry, coords)
    if r:
        return r, c

    if attrs is not None:
        attrs = attrs.split(',')

    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', '/')

    entities = None
    entity_ids = None
    if id_:
        entity_ids = [s.strip() for s in id_.split(',') if s]

    try:
        with translator_for(fiware_s) as trans:
            entities, err = trans.query(attr_names=attrs,
                                        entity_type=type_,
                                        entity_ids=entity_ids,
                                        aggr_method=aggr_method,
                                        aggr_period=aggr_period,
                                        aggr_scope=aggr_scope,
                                        from_date=from_date,
                                        to_date=to_date,
                                        last_n=last_n,
                                        limit=limit,
                                        offset=offset,
                                        idPattern=id_pattern,
                                        fiware_service=fiware_s,
                                        fiware_servicepath=fiware_sp,
                                        geo_query=geo_query)
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
        msg = "Something went wrong with QL. Error: {}".format(e)
        logging.getLogger(__name__).error(msg, exc_info=True)
        return msg, 500

    attributes = []
    entries = []
    attrs_names = []
    attrs_values = []
    ignore = ('id', 'index', 'type')

    if entities:
        for e in entities:
            attrs = [at for at in sorted(e.keys()) if at not in ignore]
            for at in attrs:
                if at not in attrs_names:
                    attrs_names.append(at)

        for at in attrs_names:
            entity_type = []
            entity_types = []
            entity_value = []
            for e in entities:
                matched_attr = lookup_string_match(e, at)
                if matched_attr is not None:
                    try:
                        f_date = dateutil.parser.isoparse(from_date).replace(
                            tzinfo=timezone.utc).isoformat()
                    except Exception as ex:
                        f_date = ''
                    try:
                        t_date = dateutil.parser.isoparse(to_date).replace(
                            tzinfo=timezone.utc).isoformat()
                    except Exception as ex:
                        t_date = ''
                    index = [
                        f_date, t_date] if aggr_method and not aggr_period else e['index']
                    entity = {
                        'entityId': e['id'],
                        'index': index,
                        'values': matched_attr['values'] if matched_attr else [],
                    }
                    if e['type'] not in entity_types:
                        entity_value = []
                        entity_value.append(entity)
                        entity_ty = {
                            'entityType': e['type'],
                            'entities': entity_value
                        }
                        entity_type.append(entity_ty)
                        entity_types.append(e['type'])
                    else:
                        entity_value.append(entity)
                        entity_type.pop()
                        entity_ty = {
                            'entityType': e['type'],
                            'entities': entity_value
                        }
                        entity_type.append(entity_ty)
            attrs_value = {
                'attrName': at,
                'types': entity_type
            }
            attrs_values.append(attrs_value)
        res = {
            'attrs': attrs_values
        }
        logging.getLogger(__name__).info("Query processed successfully")
        logging.warning(
            "usage of id and type rather than entityId and entityType from version 0.9")
        return res

    if err == "AggrMethod cannot be applied":
        r = {
            "error": "AggrMethod cannot be applied",
            "description": "AggrMethod cannot be applied on type TEXT and BOOLEAN."}
        logging.getLogger(__name__).info("AggrMethod cannot be applied")
        return r, 404

    r = {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
    logging.getLogger(__name__).info("No value found for query")
    return r, 404


def query_NTNENA_value(*args, **kwargs):
    res = query_NTNENA(*args, **kwargs)
    if isinstance(res, dict):
        res['values'] = res['attrs']
        res.pop('attrs', None)
    logging.warning(
        "usage of id and type rather than entityId and entityType from version 0.9")
    return res
