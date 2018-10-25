import os


def check_crate():
    """
    crateDB is the default backend of QuantumLeap, so it is required by
    default.
    """
    from translators.crate import CrateTranslatorInstance
    with CrateTranslatorInstance() as trans:
        crate_health = trans.get_health()
        return crate_health


def check_geocache():
    """
    Geocache is relevant only when geocoding usage is enabled.
    """
    use_geocoding = os.environ.get('USE_GEOCODING', False)
    if not use_geocoding:
        return {'status': 'pass'}

    from geocoding.geocache import GeoCodingCache
    host = os.environ.get('REDIS_HOST', None)
    port = os.environ.get('REDIS_PORT', 6379)
    gc = GeoCodingCache(host, port)
    health = gc.get_health()
    return health


def check_geocoder():
    """
    Geocoder is relevant only when geocoding usage is enabled.
    """
    use_geocoding = os.environ.get('USE_GEOCODING', False)
    if not use_geocoding:
        return {'status': 'pass'}

    from geocoding import geocoding
    health = geocoding.get_health()
    return health


def _get_http_code(res):
    if res['status'] != 'fail':
        code = 200
    else:
        code = 503
    return code


def get_health():
    """
    Return status of QuantumLeap service, taking into account status of the
    services it depends on.

    The official API specification in quantumleap.yml should document which
    services are these.

    This endpoint should be memoized (with timeout of course).
    """
    res = {}

    # Check crateDB (critical)
    health = check_crate()
    res['status'] = health['status']
    if health['status'] != 'pass':
        res.setdefault('details', {})['crateDB'] = health

    # Check geocache (critical)
    health = check_geocache()
    if health['status'] != 'pass':
        res.setdefault('details', {})['redis'] = health
        if health['status'] == 'fail' or res['status'] == 'pass':
            res['status'] = health['status']

    # Check geocoder (not critical)
    health = check_geocoder()
    if health['status'] != 'pass':
        res.setdefault('details', {})['osm'] = health
        if res['status'] == 'pass':
            res['status'] = 'warn'

    # Determine HTTP code
    code = _get_http_code(res)
    return res, code, {'Cache-Control': 'max-age=180'}
