import pytest
from geocoding.slf.geotypes import *


@pytest.mark.parametrize('lat, lon', [
    (None, 2), (1, None), (None, None)
])
def test_point_should_fail_if_none_args(lat, lon):
    with pytest.raises(ValueError):
        SlfPoint(latitude=lat, longitude=lon)


def test_point_ngsi_type():
    assert SlfPoint.ngsi_type() == 'geo:point'


def test_point_enum_points():
    point = SlfPoint(1, 2)
    expected = [[2, 1]]

    assert expected == list(point.enum_points())


def test_point_can_enum_points_many_times():
    point = SlfPoint(1, 2)
    expected = [[2, 1]]

    assert expected == list(point.enum_points())
    assert expected == list(point.enum_points())
    assert expected == list(point.enum_points())


def test_point_ngsi_attribute():
    point = SlfPoint(1, 2)
    expected = {
        'type': 'geo:point',
        'value': '1, 2'
    }

    assert expected == point.to_ngsi_attribute()


@pytest.mark.parametrize('points', [
    None, [], [SlfPoint(1, 2)]
])
def test_line_should_fail_if_invalid_points(points):
    with pytest.raises(ValueError):
        SlfLine(points)


def test_line_ngsi_type():
    assert SlfLine.ngsi_type() == 'geo:line'


def test_line_enum_points():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(5, 6)]
    line = SlfLine(points)
    expected = [[2, 1], [4, 3], [6, 5]]

    assert expected == list(line.enum_points())


def test_line_cannot_enum_points_many_times():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(5, 6)]
    line = SlfLine(points)
    expected = [[2, 1], [4, 3], [6, 5]]

    assert expected == list(line.enum_points())
    assert [] == list(line.enum_points())
    assert [] == list(line.enum_points())


def test_line_ngsi_attribute():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(5, 6)]
    line = SlfLine(points)
    expected = {
        'type': 'geo:line',
        'value': ['1, 2', '3, 4', '5, 6']
    }

    assert expected == line.to_ngsi_attribute()


@pytest.mark.parametrize('points', [
    None, [], [SlfPoint(1, 2)], [SlfPoint(1, 2), SlfPoint(1, 2)],
    [SlfPoint(1, 2), SlfPoint(1, 2), SlfPoint(1, 2)]
])
def test_polygon_should_fail_if_invalid_points(points):
    with pytest.raises(ValueError):
        SlfPolygon(points)


def test_polygon_ngsi_type():
    assert SlfPolygon.ngsi_type() == 'geo:polygon'


def test_polygon_enum_points():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(-1, 0), SlfPoint(1, 2)]
    polygon = SlfPolygon(points)
    expected = [[2, 1], [4, 3], [0, -1], [2, 1]]

    assert expected == list(polygon.enum_points())


def test_polygon_cannot_enum_points_many_times():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(-1, 0), SlfPoint(1, 2)]
    polygon = SlfPolygon(points)
    expected = [[2, 1], [4, 3], [0, -1], [2, 1]]

    assert expected == list(polygon.enum_points())
    assert [] == list(polygon.enum_points())
    assert [] == list(polygon.enum_points())


def test_polygon_ngsi_attribute():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(-1, 0), SlfPoint(1, 2)]
    polygon = SlfPolygon(points)
    expected = {
        'type': 'geo:polygon',
        'value': ['1, 2', '3, 4', '-1, 0', '1, 2']
    }

    assert expected == polygon.to_ngsi_attribute()


@pytest.mark.parametrize('points', [
    None, [], [SlfPoint(1, 2)]
])
def test_box_should_fail_if_invalid_points(points):
    with pytest.raises(ValueError):
        SlfBox(points)


def test_box_ngsi_type():
    assert SlfBox.ngsi_type() == 'geo:box'


def test_box_enum_points():
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    box = SlfBox(points)
    expected = [[2, 1], [4, 3]]

    assert expected == list(box.enum_points())


def test_box_can_enum_points_many_times():
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    box = SlfBox(points)
    expected = [[2, 1], [4, 3]]

    assert expected == list(box.enum_points())
    assert expected == list(box.enum_points())
    assert expected == list(box.enum_points())


def test_box_to_polygon():
    brc = SlfPoint(0, 1)
    tlc = SlfPoint(1, 0)
    box = SlfBox([brc, tlc])

    expected = [[0, 1], [1, 1], [1, 0], [0, 0]]
    assert expected == list(box.to_polygon().enum_points())


def test_box_ngsi_attribute():
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    box = SlfBox(points)
    expected = {
        'type': 'geo:box',
        'value': ['1, 2', '3, 4']
    }

    assert expected == box.to_ngsi_attribute()
