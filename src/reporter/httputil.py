from flask import request


def fiware_s() -> str:
    """
    Read the tenant header.
    If the request has an `ngsild-tenant` header, return its value.
    Otherwise if there's a `fiware-service` return that value. If
    none of those headers are present, return `None`. Notice if both
    headers are present, `ngsild-tenant` takes precedence.

    :return: The content of the tenant header if any.
    """
    return request.headers.get('ngsild-tenant', None) \
        or request.headers.get('fiware-service', None)


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
    sp = fiware_sp()  # cater for header not present
    # cater for whitespace around paths
    paths = {*[path.strip() for path in sp.split(',')]}
    return len(paths) == 1 and '/' in paths
