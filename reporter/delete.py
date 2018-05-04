import warnings

def delete_entity(entityId, type=None, fromDate=None, toDate=None,
                  lastN=None):
    warnings.warn(" delete_entity connexion run your_api.yaml --mock=all -v")
    return "{}".format(locals())


def delete_entities(entityType, fromDate=None, toDate=None, lastN=None):
    warnings.warn(" delete_entities connexion run your_api.yaml --mock=all -v")
    return "{}".format(locals())
