from translators.timescale_geo_query import from_ngsi_query
from geocoding.slf import *


def slf_pt() -> SlfPoint:
    return SlfPoint(1.0, 2.0)


def wkt_pt() -> str:
    return "'SRID=4326;POINT (2.0 1.0)'"


def test_near_min_max():
    query = NearQuery(geometry=slf_pt(), min_distance=10, max_distance=20)
    expected = \
        f"(not ST_DWithin(location_centroid, {wkt_pt()}, 0.00009) " + \
        f"and ST_DWithin(location_centroid, {wkt_pt()}, 0.00018))"

    assert expected == from_ngsi_query(query)


def test_near_min():
    query = NearQuery(geometry=slf_pt(), min_distance=10, max_distance=None)
    expected = f"not ST_DWithin(location_centroid, {wkt_pt()}, 0.00009)"

    assert expected == from_ngsi_query(query)


def test_near_max():
    query = NearQuery(geometry=slf_pt(), min_distance=None, max_distance=20)
    expected = f"ST_DWithin(location_centroid, {wkt_pt()}, 0.00018)"

    assert expected == from_ngsi_query(query)


def test_covered_by():
    query = CoveredByQuery(slf_pt())
    expected = f"ST_Within(location, {wkt_pt()})"

    assert expected == from_ngsi_query(query)


def test_intersects():
    query = IntersectsQuery(slf_pt())
    expected = f"ST_Intersects(location, {wkt_pt()})"

    assert expected == from_ngsi_query(query)


def test_disjoint():
    query = DisjointQuery(slf_pt())
    expected = f"ST_Disjoint(location, {wkt_pt()})"

    assert expected == from_ngsi_query(query)


def test_equals():
    query = EqualsQuery(slf_pt())
    expected = f"ST_Equals(location, {wkt_pt()})"

    assert expected == from_ngsi_query(query)
