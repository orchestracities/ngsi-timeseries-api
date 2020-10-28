from flask import request


def fiware_s() -> str:
    """
    :return: The content of the FiWare service header if any.
    """
    return request.headers.get('fiware-service', None)


def fiware_sp() -> str:
    """
    :return: The content of the FiWare service path header if any.
    """
    return request.headers.get('fiware-servicepath', None)
