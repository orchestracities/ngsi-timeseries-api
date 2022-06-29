from geocoding import geocoding
from geocoding.factory import get_geo_cache, is_geo_coding_available
from cache.factory import get_cache, is_cache_available
from translators.factory import CRATE_BACKEND, TIMESCALE_BACKEND, \
    default_backend


def check_db(db=CRATE_BACKEND):
    """
    crateDB is the default backend of QuantumLeap, so it is required by
    default.
    """
    if db == CRATE_BACKEND:
        from translators.crate import crate_translator_instance
        with crate_translator_instance() as trans:
            health = trans.get_health()
            return health
    if db == TIMESCALE_BACKEND:
        from translators.timescale import postgres_translator_instance
        with postgres_translator_instance() as trans:
            health = trans.get_health()
            return health


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

    # Check defaultDB (critical)
    db = default_backend().lower()
    try:
        res = _check_critical(check_db(db), res, db)
    except Exception:
        res['status'] = 'fail'
        res.setdefault('details', {})[db] = 'cannot reach ' + db

    # TODO add not critical check if a secondary db is configured

    # Check cache (not critical)
    res = _check_not_critical(check_cache(), res, 'redis')

    # Check geocoder (not critical)
    if with_geocoder:
        res = _check_not_critical(check_geocoder(), res, 'osm')

    # Determine HTTP code
    code = _get_http_code(res)
    return res, code, {'Cache-Control': 'max-age=180'}
