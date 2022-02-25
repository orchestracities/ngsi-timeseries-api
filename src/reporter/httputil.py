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
    return request.headers.get('fiware-servicepath', '/')


def fiware_correlator() -> str:
    """
    :return: The content of the FIWARE correlator path header if any.
    """
    return request.headers.get('Fiware-Correlator', None)

def is_root_service_path() -> bool:
    sp = fiware_sp() or ''  # cater for header not present
    paths = {*[path.strip() for path in sp.split(',')]}  # cater for whitespace around paths
    return len(paths) == 1 and '/' in paths
