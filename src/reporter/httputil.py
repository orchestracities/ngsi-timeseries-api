from flask import request


def fiware_s() -> str:
    """
    :return: The content of the FIWARE service header if any.
    """
    return request.headers.get('fiware-service', None)


def fiware_sp() -> str:
    """
    :return: The content of the FIWARE service path header if any.
    """
    return request.headers.get('fiware-servicepath', None)


def fiware_correlator() -> str:
    """
    :return: The content of the FIWARE correlator path header if any.
    """
    return request.headers.get('Fiware-Correlator', None)
