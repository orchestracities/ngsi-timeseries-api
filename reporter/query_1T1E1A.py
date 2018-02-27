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
                 offset=None):
    """
    See /entities/{entityId}/attrs/{attrName} in API Specification
    quantumleap.yml
    """
    vals = None
    with CrateTranslatorInstance() as trans:
        attr_names = [trans.TIME_INDEX, attrName]
        vals = trans.query(attr_names=attr_names,
                           entity_type=type,
                           entity_id=entityId,
                           limit=limit)
    if vals:
        res = {
            'data': {
                'entityId': entityId,
                'attrName': attrName,
                'index': [str(v[CrateTranslator.TIME_INDEX_NAME]) for v in vals],
                'values': [v[attrName]['value'] for v in vals]
            }
        }
        return res

# Before implementing the rest of these methods, move query methods to a
# different module.

def query_1T1E1A_value():
    raise NotImplementedError
