from exceptions.exceptions import AmbiguousNGSIIdError
from flask import request
from reporter.reporter import _validate_query_params
from translators.crate import CrateTranslatorInstance, CrateTranslator
import logging


def query_1TNE1A(attr_name,   # In Path
                 entity_type,
                 id_=None,  # In Query
                 aggr_method=None,
                 aggr_period=None,
                 options=None,
                 from_date=None,
                 to_date=None,
                 last_n=None,
                 limit=10000,
                 offset=0):
    """
    See /types/{entityType}/attrs/{attrName} in API Specification
    quantumleap.yml
    """
    r, c = _validate_query_params(aggr_period,
                                  aggr_method,
                                  [attr_name],
                                  options)
    if c != 200:
        return r, c

    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    entities = None
    entity_ids = None
    if id_:
        entity_ids = [s.strip() for s in id_.split(',') if s]
    try:
        with CrateTranslatorInstance() as trans:
            entities = trans.query(attr_names=[attr_name],
                                   entity_type=entity_type,
                                   entity_ids=entity_ids,
                                   aggr_method=aggr_method,
                                   from_date=from_date,
                                   to_date=to_date,
                                   last_n=last_n,
                                   limit=limit,
                                   offset=offset,
                                   fiware_service=fiware_s,
                                   fiware_servicepath=fiware_sp,)
    except AmbiguousNGSIIdError as e:
        return {
            "error": "AmbiguousNGSIIdError",
            "description": str(e)
        }, 409

    except Exception as e:
        # Temp workaround to debug test_not_found
        msg = "Something went wrong with QL. Error: {}".format(e)
        logging.getLogger().error(msg, exc_info=True)
        return msg, 500

    if entities:
        res = _prepare_response(entities,
                                attr_name,
                                entity_type,
                                entity_ids,
                                aggr_method,
                                from_date,
                                to_date,)
        return res

    r = {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
    return r, 404


def _prepare_response(entities, attr_name, entity_type, entity_ids,
                      aggr_method, from_date, to_date):
    values = {}
    for e in entities:
        e_values = values.setdefault(e['id'], [])
        e_values.append(e[attr_name]['value'])

    if aggr_method:
        # Use fromDate / toDate
        indexes = [from_date or '', to_date or '']
    else:
        # Use entity's time_index
        indexes = {}
        for e in entities:
            e_index = indexes.setdefault(e['id'], [])
            e_index.append(str(e[CrateTranslator.TIME_INDEX_NAME]))

    # Preserve given order of ids (if any)
    entries = []
    if entity_ids:
        for ei in entity_ids:
            if ei in values:
                index = indexes if aggr_method else indexes[ei]
                i = {
                    'entityId': ei,
                    'index': index,
                    'values': values[ei],
                }
                entries.append(i)
                values.pop(ei)

    # Proceed with the rest of the values in order of keys
    for e_id in sorted(values.keys()):
        index = [] if aggr_method else indexes[e_id]
        i = {
            'entityId': e_id,
            'index': index,
            'values': values[e_id],
        }
        entries.append(i)

    res = {
        'data': {
            'entityType': entity_type,
            'attrName': attr_name,
            'entities': entries,
        }
    }
    return res


def query_1TNE1A_value(*args, **kwargs):
    res = query_1TNE1A(*args, **kwargs)
    if isinstance(res, dict) and 'data' in res:
        res['data'].pop('entityType')
        res['data'].pop('attrName')
        res['data']['values'] = res['data']['entities']
        res['data'].pop('entities')
    return res
