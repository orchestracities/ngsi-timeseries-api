from geocoding.slf import *
from sql.ast.crate import *
import pytest


@pytest.mark.parametrize('match_type, match_fn', [
    ('intersects', intersects), ('disjoint', disjoint), ('within', within)
])
def test_match_point(match_type, match_fn):
    point = SlfPoint(1, 2)
    expected = f"match (x, 'POINT (2 1)') using {match_type}"

    actual = match_fn('x', point).eval()
    assert expected == actual


@pytest.mark.parametrize('match_type, match_fn', [
    ('intersects', intersects), ('disjoint', disjoint), ('within', within)
])
def test_match_line(match_type, match_fn):
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    line = SlfLine(points)
    expected = f"match (x, 'LINESTRING (2 1, 4 3)') using {match_type}"

    actual = match_fn('x', line).eval()
    assert expected == actual


def test_distance():
    point = SlfPoint(1, 2)
    expected = "distance(x, 'POINT (2 1)')"

    actual = distance('x', point).eval()
    assert expected == actual
