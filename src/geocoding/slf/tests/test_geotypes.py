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

    expected = [[0, 1], [1, 1], [1, 0], [0, 0], [0, 1]]
    assert expected == list(box.to_polygon().enum_points())


def test_box_ngsi_attribute():
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    box = SlfBox(points)
    expected = {
        'type': 'geo:box',
        'value': ['1, 2', '3, 4']
    }

    assert expected == box.to_ngsi_attribute()


@pytest.mark.parametrize('ngsi_data', [
    None, '{}', {}, {'type': 'geo:line'},
    {'type': 'geo:point'},
    {'type': 'geo:point', 'value': None},
    {'type': 'geo:point', 'value': ''},
    {'type': 'geo:point', 'value': ','},
    {'type': 'geo:point', 'value': ', 2'},
    {'type': 'geo:point', 'value': '1'},
    {'type': 'geo:point', 'value': '1,'},
    {'type': 'geo:point', 'value': '1,?'},
    {'type': 'geo:point', 'value': [1, 2]}
])
def test_point_from_invalid_ngsi_dict(ngsi_data):
    assert SlfPoint.from_ngsi_dict(ngsi_data) is None


@pytest.mark.parametrize('ngsi_data', [
    {'type': 'geo:point', 'value': '1.0, 2.0'},
    {'type': 'geo:point', 'value': '1.2, -3.4'}
])
def test_point_from_ngsi_dict(ngsi_data):
    ast = SlfPoint.from_ngsi_dict(ngsi_data)
    assert ast.to_ngsi_attribute() == ngsi_data


@pytest.mark.parametrize('ngsi_data', [
    None, '{}', {}, {'type': 'geo:point'},
    {'type': 'geo:line'},
    {'type': 'geo:line', 'value': None},
    {'type': 'geo:line', 'value': ''},
    {'type': 'geo:line', 'value': {}},
    {'type': 'geo:line', 'value': [', 2']},
    {'type': 'geo:line', 'value': ['1']},
    {'type': 'geo:line', 'value': ['1,']},
    {'type': 'geo:line', 'value': ['1,?']},
    {'type': 'geo:line', 'value': ['1,2', '']},
    {'type': 'geo:line', 'value': ['1,2', '', '3,4']},
    {'type': 'geo:line', 'value': ['1,2', '3,4', '']},
    {'type': 'geo:line', 'value': ['1,2', 3, 4]}
])
def test_line_from_invalid_ngsi_dict(ngsi_data):
    assert SlfLine.from_ngsi_dict(ngsi_data) is None


@pytest.mark.parametrize('ngsi_data', [
    {'type': 'geo:line', 'value': ['1.0, 2.0', '3.0, 4.0']},
    {'type': 'geo:line', 'value': ['1.0, 2.0', '3.0, 4.0', '5.0, 6.0']}
])
def test_line_from_ngsi_dict(ngsi_data):
    ast = SlfLine.from_ngsi_dict(ngsi_data)
    assert ast.to_ngsi_attribute() == ngsi_data


@pytest.mark.parametrize('ngsi_data', [
    None, '{}', {}, {'type': 'geo:point'},
    {'type': 'geo:polygon'},
    {'type': 'geo:polygon', 'value': None},
    {'type': 'geo:polygon', 'value': ''},
    {'type': 'geo:polygon', 'value': {}},
    {'type': 'geo:polygon', 'value': [', 2']},
    {'type': 'geo:polygon', 'value': ['1']},
    {'type': 'geo:polygon', 'value': ['1,']},
    {'type': 'geo:polygon', 'value': ['1,?']},
    {'type': 'geo:polygon', 'value': ['1,2', '']},
    {'type': 'geo:polygon', 'value': ['1,2', '', '3,4']},
    {'type': 'geo:polygon', 'value': ['1,2', '3,4', '']},
    {'type': 'geo:polygon', 'value': ['1,2', 3, 4]},
    {'type': 'geo:polygon', 'value': ['1,2', '3,4']}
])
def test_polygon_from_invalid_ngsi_dict(ngsi_data):
    assert SlfPolygon.from_ngsi_dict(ngsi_data) is None


@pytest.mark.parametrize('ngsi_data', [
    {'type': 'geo:polygon', 'value': ['1.0, 2.0', '3.0, 4.0', '5.0, 6.0',
                                      '7.0, 8.0', '9.0, 10.0']},
    {'type': 'geo:polygon', 'value': ['1.0, 2.0', '3.0, 4.0', '5.0, 6.0',
                                      '7.0, 8.0', '9.0, 10.0', '1.0, 2.0']}
])
def test_polygon_from_ngsi_dict(ngsi_data):
    ast = SlfPolygon.from_ngsi_dict(ngsi_data)
    assert ast.to_ngsi_attribute() == ngsi_data


@pytest.mark.parametrize('ngsi_data', [
    None, '{}', {}, {'type': 'geo:point'},
    {'type': 'geo:box'},
    {'type': 'geo:box', 'value': None},
    {'type': 'geo:box', 'value': ''},
    {'type': 'geo:box', 'value': {}},
    {'type': 'geo:box', 'value': [', 2']},
    {'type': 'geo:box', 'value': ['1']},
    {'type': 'geo:box', 'value': ['1,']},
    {'type': 'geo:box', 'value': ['1,?']},
    {'type': 'geo:box', 'value': ['1,2', '']},
    {'type': 'geo:box', 'value': ['1,2', '', '3,4']},
    {'type': 'geo:box', 'value': ['1,2', '3,4', '']},
    {'type': 'geo:box', 'value': ['1,2', 3, 4]}
])
def test_box_from_invalid_ngsi_dict(ngsi_data):
    assert SlfBox.from_ngsi_dict(ngsi_data) is None


@pytest.mark.parametrize('ngsi_data', [
    {'type': 'geo:box', 'value': ['1.0, 2.0', '3.0, 4.0']}
])
def test_box_from_ngsi_dict(ngsi_data):
    ast = SlfBox.from_ngsi_dict(ngsi_data)
    assert ast.to_ngsi_attribute() == ngsi_data


@pytest.mark.parametrize('ngsi_data, slf_type', [
    ({'type': 'geo:point', 'value': '1.0, 2.0'}, SlfPoint),
    ({'type': 'geo:line', 'value': ['1.0, 2.0', '3.0, 4.0']}, SlfLine),
    ({'type': 'geo:polygon', 'value': ['1.0, 2.0', '3.0, 4.0', '5.0, 6.0',
                                       '7.0, 8.0', '9.0, 10.0']}, SlfPolygon),
    ({'type': 'geo:box', 'value': ['1.0, 2.0', '3.0, 4.0']}, SlfBox)
])
def test_build_from_ngsi_dict(ngsi_data, slf_type):
    ast = SlfGeometry.build_from_ngsi_dict(ngsi_data)
    assert isinstance(ast, slf_type)
    assert ast.to_ngsi_attribute() == ngsi_data


@pytest.mark.parametrize('ngsi_data, expected', [
    ({'type': 'geo:point'}, True),
    ({'type': 'geo:line', 'value': ['1.0, 2.0', '3.0, 4.0']}, True),
    ({'type': 'geo:polygon', 'value': []}, True),
    ({'type': 'geo:box', 'value': None}, True),
    (None, False), ('', False), ({}, False)
])
def test_is_ngsi_slf_attr(ngsi_data, expected):
    assert SlfGeometry.is_ngsi_slf_attr(ngsi_data) == expected
