import pytest

from geocoding.slf import *
from sql.ast.timescale import *


@pytest.mark.parametrize('incidence_type, incidence_fn', [
    (GeoIncidenceType.EQUAL.value, equals),
    (GeoIncidenceType.INTERSECTS.value, intersects),
    (GeoIncidenceType.DISJOINT.value, disjoint),
    (GeoIncidenceType.WITHIN.value, within)
])
def test_point_incidence(incidence_type, incidence_fn):
    point = SlfPoint(1, 2)
    expected = f"{incidence_type}(x, 'SRID=4326;POINT (2 1)')"

    actual = incidence_fn('x', point).eval()
    assert actual == expected


@pytest.mark.parametrize('incidence_type, incidence_fn', [
    (GeoIncidenceType.EQUAL.value, equals),
    (GeoIncidenceType.INTERSECTS.value, intersects),
    (GeoIncidenceType.DISJOINT.value, disjoint),
    (GeoIncidenceType.WITHIN.value, within)
])
def test_line_incidence(incidence_type, incidence_fn):
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    line = SlfLine(points)
    expected = f"{incidence_type}(x, 'SRID=4326;LINESTRING (2 1, 4 3)')"

    actual = incidence_fn('x', line).eval()
    assert actual == expected


def test_distance():
    point = SlfPoint(1, 2)
    dist = 10
    expected = f"ST_DWithin(x, 'SRID=4326;POINT (2 1)', {dist})"

    actual = distance('x', point, dist).eval()
    assert actual == expected
