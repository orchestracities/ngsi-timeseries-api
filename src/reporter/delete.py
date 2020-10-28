from exceptions.exceptions import AmbiguousNGSIIdError
from .httputil import fiware_s, fiware_sp
from translators.factory import translator_for


def delete_entity(entity_id, type_=None, from_date=None, to_date=None):
    try:
        with translator_for(fiware_s()) as trans:
            deleted = trans.delete_entity(eid=entity_id,
                                          etype=type_,
                                          from_date=from_date,
                                          to_date=to_date,
                                          fiware_service=fiware_s(),
                                          fiware_servicepath=fiware_sp(),)
    except AmbiguousNGSIIdError as e:
        return {
            "error": "AmbiguousNGSIIdError",
            "description": str(e)
        }, 409

    if deleted == 0:
        r = {
            "error": "Not Found",
            "description": "No records were found for such query."
        }
        return r, 404

    if deleted > 0:
        return '{} records successfully deleted.'.format(deleted), 204


def delete_entities(entity_type, from_date=None, to_date=None,
                    drop_table=False):
    with translator_for(fiware_s()) as trans:
        if drop_table:
            trans.drop_table(etype=entity_type, fiware_service=fiware_s())
            return 'entity table dropped', 204

        deleted = trans.delete_entities(etype=entity_type,
                                        from_date=from_date,
                                        to_date=to_date,
                                        fiware_service=fiware_s(),
                                        fiware_servicepath=fiware_sp(),)
        if deleted == 0:
            r = {
                "error": "Not Found",
                "description": "No records were found for such query."
            }
            return r, 404

        if deleted > 0:
            return '{} records successfully deleted.'.format(deleted), 204
