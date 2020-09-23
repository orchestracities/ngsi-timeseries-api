from exceptions.exceptions import AmbiguousNGSIIdError
from .http import fiware_s, fiware_sp
from translators import crate


def delete_entity(entity_id, type_=None, from_date=None, to_date=None):
    try:
        with crate.CrateTranslatorInstance() as trans:
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


def delete_entities(entity_type, from_date=None, to_date=None):
    with crate.CrateTranslatorInstance() as trans:
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


def drop_entity_storage(entity_type: str):
    with crate.CrateTranslatorInstance() as trans:
        trans.drop_table(etype=entity_type, fiware_service=fiware_s())
