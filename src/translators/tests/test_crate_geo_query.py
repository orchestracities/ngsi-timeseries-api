from translators.crate_geo_query import from_ngsi_query
from geocoding.slf import *


def test_near_min_max():
    geom = SlfPoint(1, 2)
    query = NearQuery(geometry=geom, min_distance=10, max_distance=20)
    expected = "((distance(location_centroid, 'POINT (2.0 1.0)') >= 10) " + \
               "and (distance(location_centroid, 'POINT (2.0 1.0)') <= 20))"

    assert expected == from_ngsi_query(query)


def test_near_min():
    geom = SlfPoint(1, 2)
    query = NearQuery(geometry=geom, min_distance=10, max_distance=None)
    expected = "(distance(location_centroid, 'POINT (2.0 1.0)') >= 10)"

    assert expected == from_ngsi_query(query)


def test_near_max():
    geom = SlfPoint(1, 2)
    query = NearQuery(geometry=geom, min_distance=None, max_distance=20)
    expected = "(distance(location_centroid, 'POINT (2.0 1.0)') <= 20)"

    assert expected == from_ngsi_query(query)


def test_covered_by():
    geom = SlfPoint(1, 2)
    query = CoveredByQuery(geom)
    expected = "match (location, 'POINT (2 1)') using within"

    assert expected == from_ngsi_query(query)


def test_intersects():
    geom = SlfPoint(1, 2)
    query = IntersectsQuery(geom)
    expected = "match (location, 'POINT (2 1)') using intersects"

    assert expected == from_ngsi_query(query)


def test_disjoint():
    geom = SlfPoint(1, 2)
    query = DisjointQuery(geom)
    expected = "match (location, 'POINT (2 1)') using disjoint"

    assert expected == from_ngsi_query(query)


def test_equals():
    geom = SlfPoint(1, 2)
    query = EqualsQuery(geom)
    expected = "match (location, 'POINT (2 1)') using within and " + \
               "within('POINT (2 1)', location)"

    assert expected == from_ngsi_query(query)
