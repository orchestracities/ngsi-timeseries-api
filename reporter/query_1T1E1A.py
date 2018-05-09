from flask import request
from translators.crate import CrateTranslatorInstance, CrateTranslator


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
                 offset=0):
    """
    See /entities/{entityId}/attrs/{attrName} in API Specification
    quantumleap.yml
    """
    if type_ is None:
        r = {
            "error": "Not Implemented",
            "description": "For now, you must always specify entity type."
        }
        return r, 400

    if options or aggr_period:
        import warnings
        warnings.warn("Unimplemented query parameters: options, aggrPeriod")

    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    entities = None
    with CrateTranslatorInstance() as trans:
        entities = trans.query(attr_names=[attr_name],
                           entity_type=type_,
                           entity_id=entity_id,
                           aggr_method=aggr_method,
                           from_date=from_date,
                           to_date=to_date,
                           last_n=last_n,
                           limit=limit,
                           offset=offset,
                           fiware_service=fiware_s,
                           fiware_servicepath=fiware_sp,)
    if entities:
        if aggr_method:
            index = []
        else:
            index = [str(e[CrateTranslator.TIME_INDEX_NAME]) for e in entities]
        res = {
            'data': {
                'entityId': entity_id,
                'attrName': attr_name,
                'index': index,
                'values': [e[attr_name]['value'] for e in entities]
            }
        }
        return res

    r = {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
    return r, 404


def query_1T1E1A_value(*args, **kwargs):
    res = query_1T1E1A(*args, **kwargs)
    if isinstance(res, dict) and 'data' in res:
        res['data'].pop('entityId')
        res['data'].pop('attrName')
        return res
    return res
