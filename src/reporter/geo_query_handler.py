from geocoding.slf import from_geo_params, EqualsQuery


invalid_params = {
    'error': 'ValueError',
    'description': 'Invalid geographical query parameters'
}, 400, None

query_not_supported = {
    'error': 'NotSupportedQuery',
    'description': 'This geographical query is not supported'
}, 422, None


def handle_geo_query(georel=None, geometry=None, coords=None):
    try:

        geo_query = from_geo_params(georel, geometry, coords)
        if isinstance(geo_query, EqualsQuery):  # see note below
            return query_not_supported
        return None, 0, geo_query

    except ValueError:
        return invalid_params

# NOTE. Equals query support.
# We actually have all the bits and pieces in place to do this, except Crate
# doesn't like the query we generate, since the within function only seems to
# work with a first argument of geo_point even though the docs state it should
# work with any shape. I opened an issue about it in the Crate repo:
#
#   - https://github.com/crate/crate/issues/7997
#
# after they fix the issue, zap the if block above to re-enable equals queries.
