from flask import request
from translators.crate import CrateTranslatorInstance


def delete_entity(entity_id, type_=None, from_date=None, to_date=None):
    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    with CrateTranslatorInstance() as trans:
        r = trans.delete_entity(entity_id=entity_id,
                                entity_type=type_,
                                from_date=from_date,
                                to_date=to_date,
                                fiware_service=fiware_s,
                                fiware_servicepath=fiware_sp,)
        # if r < 0 -> connexion handles 500
        if r == 0:
            return 'Not Found', 404

        if r > 0:
            return '{} records successfully deleted.'.format(r), 204


def delete_entities(entity_type, from_date=None, to_date=None):
    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    with CrateTranslatorInstance() as trans:
        r = trans.delete_entities(entity_type=entity_type,
                                  from_date=from_date,
                                  to_date=to_date,
                                  fiware_service=fiware_s,
                                  fiware_servicepath=fiware_sp,)
        # if r < 0 -> connexion handles 500
        if r == 0:
            return 'Not Found', 404

        if r > 0:
            return '{} records successfully deleted.'.format(r), 204
