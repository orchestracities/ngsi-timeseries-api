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


def _check_not_critical(health, res, service):
    if health['status'] != 'pass':
        res.setdefault('details', {})[service] = health
        if res['status'] == 'pass':
            res['status'] = 'warn'
    return res


def _check_critical(health, res, service):
    if health['status'] != 'pass':
        res['status'] = health['status']
        res.setdefault('details', {})[service] = health
    return res


def get_health(with_geocoder=False):
    """
    Return status of QuantumLeap service, taking into account status of the
    services it depends on.

    The official API specification in quantumleap.yml should document which
    services are these.

    This endpoint should be memoized (with timeout of course).
    """
    res = {
        'status': 'pass'
    }

    # Check crateDB (critical)
    try:
        res = _check_critical(check_crate(), res, 'crateDB')
    except Exception:
        res['status'] = 'fail'
        res.setdefault('details', {})['crateDB'] = 'cannot reach crate'

    # Check cache (not critical)
    res = _check_not_critical(check_cache(), res, 'redis')

    # Check geocoder (not critical)
    if with_geocoder:
        res = _check_not_critical(check_geocoder(), res, 'osm')

    # Determine HTTP code
    code = _get_http_code(res)
    return res, code, {'Cache-Control': 'max-age=180'}
