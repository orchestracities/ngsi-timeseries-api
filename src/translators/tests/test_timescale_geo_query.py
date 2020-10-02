from translators.timescale_geo_query import from_ngsi_query
from geocoding.slf import *


def test_near_min_max():
    geom = SlfPoint(1, 2)
    query = NearQuery(geometry=geom, min_distance=10, max_distance=20)
    expected = \
        "(not ST_DWithin(location_centroid, 'POINT (2.0 1.0)', 0.00009) " + \
        "and ST_DWithin(location_centroid, 'POINT (2.0 1.0)', 0.00018))"

    assert expected == from_ngsi_query(query)


def test_near_min():
    geom = SlfPoint(1, 2)
    query = NearQuery(geometry=geom, min_distance=10, max_distance=None)
    expected = "not ST_DWithin(location_centroid, 'POINT (2.0 1.0)', 0.00009)"

    assert expected == from_ngsi_query(query)


def test_near_max():
    geom = SlfPoint(1, 2)
    query = NearQuery(geometry=geom, min_distance=None, max_distance=20)
    expected = "ST_DWithin(location_centroid, 'POINT (2.0 1.0)', 0.00018)"

    assert expected == from_ngsi_query(query)


def test_covered_by():
    geom = SlfPoint(1, 2)
    query = CoveredByQuery(geom)
    expected = "ST_Within(location, 'POINT (2 1)')"

    assert expected == from_ngsi_query(query)


def test_intersects():
    geom = SlfPoint(1, 2)
    query = IntersectsQuery(geom)
    expected = "ST_Intersects(location, 'POINT (2 1)')"

    assert expected == from_ngsi_query(query)


def test_disjoint():
    geom = SlfPoint(1, 2)
    query = DisjointQuery(geom)
    expected = "ST_Disjoint(location, 'POINT (2 1)')"

    assert expected == from_ngsi_query(query)


def test_equals():
    geom = SlfPoint(1, 2)
    query = EqualsQuery(geom)
    expected = "ST_Equals(location, 'POINT (2 1)')"

    assert expected == from_ngsi_query(query)
