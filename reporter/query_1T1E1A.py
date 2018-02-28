from translators.crate import CrateTranslatorInstance, CrateTranslator


def query_1T1E1A(attrName,   # In Path ↧
                 entityId,
                 type=None,  # In Query ↧
                 aggrMethod=None,
                 aggrPeriod=None,
                 options=None,
                 fromDate=None,
                 toDate=None,
                 lastN=None,
                 limit=10000,
                 offset=0):
    """
    See /entities/{entityId}/attrs/{attrName} in API Specification
    quantumleap.yml
    """
    if options or aggrPeriod:
        import warnings
        warnings.warn("Unimplemented query parameters: options, aggrPeriod")

    vals = None
    with CrateTranslatorInstance() as trans:
        vals = trans.query(attr_names=[attrName],
                           entity_type=type,
                           entity_id=entityId,
                           aggrMethod=aggrMethod,
                           fromDate=fromDate,
                           toDate=toDate,
                           lastN=lastN,
                           limit=limit,
                           offset=offset)
    if vals:
        if aggrMethod:
            index = []
        else:
            index = [str(v[CrateTranslator.TIME_INDEX_NAME]) for v in vals]
        res = {
            'data': {
                'entityId': entityId,
                'attrName': attrName,
                'index': index,
                'values': [v[attrName]['value'] for v in vals]
            }
        }
        return res


def query_1T1E1A_value(*args, **kwargs):
    res = query_1T1E1A(*args, **kwargs)
    if res:
        res['data'].pop('entityId')
        res['data'].pop('attrName')
    return res
