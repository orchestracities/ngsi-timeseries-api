from functools import reduce
from geocoding.slf import *
from geocoding.location import CENTROID_ATTR_NAME, LOCATION_ATTR_NAME
from sql.ast.crate import *


def from_near_query(query: NearQuery) -> Term:
    min_d = query.min_distance()
    max_d = query.max_distance()

    min_q = distance(CENTROID_ATTR_NAME, query.centroid()) >= min_d \
        if min_d is not None else None
    max_q = distance(CENTROID_ATTR_NAME, query.centroid()) <= max_d \
        if max_d is not None else None

    qs = filter(lambda x: x is not None, [min_q, max_q])
    return reduce(lambda t, q: t & q, qs)
# NOTE. This ^ assumes at least one of min_d, max_d is there which is the case
# otherwise the query parser would've thrown an exception.


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
