from flask import request
from translators.crate import CrateTranslatorInstance, CrateTranslator


def query_1T1ENA(entityId,   # In Path
                 type=None,  # In Query ↧
                 attrs=None,
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

    if aggrMethod and not attrs:
        msg = "Specified aggrMethod = {} but missing attrs parameter."
        return msg.format(aggrMethod), 400

    if attrs is not None:
        attrs = attrs.split(',')

    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    entities = None
    with CrateTranslatorInstance() as trans:
        entities = trans.query(attr_names=attrs,
                           entity_type=type,
                           entity_id=entityId,
                           aggrMethod=aggrMethod,
                           fromDate=fromDate,
                           toDate=toDate,
                           lastN=lastN,
                           limit=limit,
                           offset=offset,
                           fiware_service=fiware_s,
                           fiware_servicepath=fiware_sp,)
    if entities:
        if aggrMethod:
            index = []
        else:
            index = [str(e[CrateTranslator.TIME_INDEX_NAME]) for e in entities]

        ignore = ('type', 'id', CrateTranslator.TIME_INDEX_NAME)
        attrs = [at for at in sorted(entities[0].keys()) if at not in ignore]

        attributes = []
        for at in attrs:
            attributes.append({
                'attrName': at,
                'values': []
            })

        for i, at in enumerate(attrs):
            for e in entities:
                attributes[i]['values'].append(e[at]['value'])

        res = {
            'data': {
                'entityId': entityId,
                'index': index,
                'attributes': attributes
            }
        }
        return res


def query_1T1ENA_value(*args, **kwargs):
    res = query_1T1ENA(*args, **kwargs)
    if res:
        res['data'].pop('entityId')
    return res
