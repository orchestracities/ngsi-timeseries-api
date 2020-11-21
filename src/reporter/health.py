import os

from geocoding import geocoding
from geocoding.factory import get_geo_cache, is_geo_coding_available
from cache.factory import get_cache, is_cache_available


# TODO having now multiple backends, health check needs update
def check_crate():
    """
    crateDB is the default backend of QuantumLeap, so it is required by
    default.
    """
    from translators.crate import CrateTranslatorInstance
    with CrateTranslatorInstance() as trans:
        crate_health = trans.get_health()
        return crate_health


def check_cache():
    """
    Cache check.
    """
    if not is_cache_available():
        return {'status': 'pass'}

    cache = get_cache()
    return cache.get_health()


def check_geocoder():
    """
    Geocoder is relevant only when geocoding usage is enabled.
    """
    if not is_geo_coding_available():
        return {'status': 'pass'}

    return geocoding.get_health()


def _get_http_code(res):
    if res['status'] != 'fail':
        code = 200
    else:
        code = 503
    return code


def get_health(with_geocoder=False):
    """
    Return status of QuantumLeap service, taking into account status of the
    services it depends on.

    The official API specification in quantumleap.yml should document which
    services are these.

    This endpoint should be memoized (with timeout of course).
    """
    res = {}

    # Check crateDB (critical)
    try:
        health = check_crate()
        res['status'] = health['status']
        if health['status'] != 'pass':
            res.setdefault('details', {})['crateDB'] = health
    except Exception:
        res['status'] = 'fail'
        res.setdefault('details', {})['crateDB'] = 'cannot reach crate'

    # Check cache (not critical)
    health = check_cache()
    if health['status'] != 'pass':
        res.setdefault('details', {})['redis'] = health
        if res['status'] == 'pass':
            res['status'] = 'warn'

    # Check geocoder (not critical)
    if with_geocoder:
        health = check_geocoder()
        if health['status'] != 'pass':
            res.setdefault('details', {})['osm'] = health
            if res['status'] == 'pass':
                res['status'] = 'warn'

    # Determine HTTP code
    code = _get_http_code(res)
    return res, code, {'Cache-Control': 'max-age=180'}
