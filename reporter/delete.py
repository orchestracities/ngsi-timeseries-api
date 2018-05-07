from flask import request
from translators.crate import CrateTranslatorInstance


def delete_entity(entityId, type=None, fromDate=None, toDate=None):
    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    with CrateTranslatorInstance() as trans:
        r = trans.delete_entity(entity_id=entityId,
                                entity_type=type,
                                from_date=fromDate,
                                to_date=toDate,
                                fiware_service=fiware_s,
                                fiware_servicepath=fiware_sp,)
        # if r < 0 -> connexion handles 500
        if r == 0:
            return 'Not Found', 404

        if r > 0:
            return '{} records successfully deleted.'.format(r), 204


def delete_entities(entityType, fromDate=None, toDate=None):
    fiware_s = request.headers.get('fiware-service', None)
    fiware_sp = request.headers.get('fiware-servicepath', None)

    with CrateTranslatorInstance() as trans:
        r = trans.delete_entities(entity_type=entityType,
                                  from_date=fromDate,
                                  to_date=toDate,
                                  fiware_service=fiware_s,
                                  fiware_servicepath=fiware_sp,)
        # if r < 0 -> connexion handles 500
        if r == 0:
            return 'Not Found', 404

        if r > 0:
            return '{} records successfully deleted.'.format(r), 204
