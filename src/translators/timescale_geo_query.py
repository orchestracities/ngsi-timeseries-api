from functools import reduce
from geocoding.slf import *
from geocoding.location import CENTROID_ATTR_NAME, LOCATION_ATTR_NAME
from sql.ast.timescale import *


def from_near_query(query: NearQuery) -> Term:
    def within_distance_of(length_in_m: float) -> GeoDistanceTerm:
        length_in_dd = 0.000009 * length_in_m  # see (1) and (2) below
        return distance(CENTROID_ATTR_NAME, query.centroid(), length_in_dd)

    min_d = query.min_distance()
    max_d = query.max_distance()

    min_q = ~within_distance_of(min_d) if min_d is not None else None
    max_q = within_distance_of(max_d) if max_d is not None else None

    qs = filter(lambda x: x is not None, [min_q, max_q])
    return reduce(lambda t, q: t & q, qs)  # see (3) below
# NOTES.
# 1. Nasty dependencies. The distance function is implemented in terms of
# PostGIS's ST_DWithin function which takes a distance expressed in the
# same units as those of the spatial ref sys of the queried geometries.
# Since the query centroid is computed out of points in the WGS84 ref, that
# should also be the ref sys the translator specifies when inserting location
# centroids.
# 2. Speed vs accuracy. The way we compute centroids isn't really accurate for
# large geographical shapes (e.g. a nation) but the computation is simple, fast
# and works decently for small shapes. The exact same argument applies to the
# conversion from metres to degrees---not sound really but works decently for
# small radius search, like 10 or 20km. Another area where we favoured speed
# over accuracy is the use of ST_DWithin: it's faster than other options (well,
# provided a geo index is defined on the geometry columns) but not as accurate.
# ST_DistanceSphere (or ST_DistanceSpheroid) would be a better choice for
# accuracy, avoid us the (lame!!) conversion to decimal degrees and simplify
# the generated SQL.
# 3. Near query validation. The reduce function bombs out on an empty list
# if no initial value is given. In our case this isn't possible, i.e. at
# least one of min_d, max_d is there since near query validation throws an
# exception otherwise.


def from_covered_by_query(query: CoveredByQuery) -> Term:
    return within(LOCATION_ATTR_NAME, query.reference_shape())


def from_intersects_query(query: IntersectsQuery) -> Term:
    return intersects(LOCATION_ATTR_NAME, query.reference_shape())


def from_disjoint_query(query: DisjointQuery) -> Term:
    return disjoint(LOCATION_ATTR_NAME, query.reference_shape())


def from_equals_query(query: EqualsQuery) -> Term:
    return equals(LOCATION_ATTR_NAME, query.reference_shape())


def from_ngsi_query(query: SlfQuery) -> Optional[str]:
    query_builders = [(NearQuery, from_near_query),
                      (CoveredByQuery, from_covered_by_query),
                      (IntersectsQuery, from_intersects_query),
                      (DisjointQuery, from_disjoint_query),
                      (EqualsQuery, from_equals_query)]
    for b in query_builders:
        if isinstance(query, b[0]):
            return b[1](query).eval()

    return None
