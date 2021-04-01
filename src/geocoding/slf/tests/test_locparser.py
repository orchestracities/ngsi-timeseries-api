import pytest
from geocoding.slf.locparser import *


@pytest.mark.parametrize('ngsi_geom_type', [
    None, '', 'geo:???', 'geo: ', 'geo: line'  # note the space!
])
def test_lookup_parser_return_fail_parser_on_unknown_geom(ngsi_geom_type):
    parser = lookup_parser(ngsi_geom_type)
    assert parser is not None

    entity_with_valid_location = {
        'location': {
            'value': '41.3763726, 2.186447514',
            'type': 'geo:point'
        }
    }
    parsed = parser(entity_with_valid_location)
    assert parsed is None


@pytest.mark.parametrize('value', [
    None, 3, {}, []
])
def test_point_from_wgs84_should_fail_if_arg_not_str(value):
    with pytest.raises(TypeError):
        point_from_wgs84(value)


@pytest.mark.parametrize('invalid_point', [
    '1,2x', '1,', ',2 ', ''
])
def test_point_from_wgs84_should_fail_on_non_numeric_coords(invalid_point):
    with pytest.raises(ValueError):
        point_from_wgs84(invalid_point)


@pytest.mark.parametrize('wgs84_point', [
    '1.1,2', ' 1.1,2', '1.1,2 ', '1.1, 2', ' 1.1 , 2 ', '\t1.1, \t2'
])
def test_point_from_wgs84_can_handle_whitespace(wgs84_point):
    actual = point_from_wgs84(wgs84_point)

    assert actual.latitude() == 1.1
    assert actual.longitude() == 2


def test_points_from_wgs84_should_fail_on_none():
    with pytest.raises(TypeError):
        list(points_from_wgs84(None))


def test_points_from_wgs84():
    actual = list(points_from_wgs84(['1,2', '3,4']))

    assert len(actual) == 2
    assert actual[0].latitude() == 1
    assert actual[0].longitude() == 2
    assert actual[1].latitude() == 3
    assert actual[1].longitude() == 4


def test_parse_ngsi_point():
    actual = from_location_attribute('geo:point', '1, 2')

    assert actual is not None
    assert isinstance(actual, SlfPoint)
    assert actual.latitude() == 1
    assert actual.longitude() == 2


def test_parse_ngsi_line():
    actual = from_location_attribute('geo:line', ['1, 2', '3,4'])

    assert actual is not None
    assert isinstance(actual, SlfLine)

    points = list(actual._points())
    assert len(points) == 2
    assert points[0].latitude() == 1
    assert points[0].longitude() == 2
    assert points[1].latitude() == 3
    assert points[1].longitude() == 4

    assert [] == list(actual.enum_points())  # already consumed stream above


def test_parse_ngsi_polygon():
    actual = from_location_attribute('geo:polygon',
                                     ['1, 2', '3,4', '-1,-1', '1,2'])

    assert actual is not None
    assert isinstance(actual, SlfPolygon)

    points = list(actual._points())
    assert len(points) == 4
    assert points[0].latitude() == 1
    assert points[0].longitude() == 2
    assert points[1].latitude() == 3
    assert points[1].longitude() == 4
    assert points[2].latitude() == -1
    assert points[2].longitude() == -1
    assert points[3].latitude() == 1
    assert points[3].longitude() == 2

    assert [] == list(actual.enum_points())  # already consumed stream above


def test_parse_ngsi_box():
    actual = from_location_attribute('geo:box', ['1, 2', '3,4'])

    assert actual is not None
    assert isinstance(actual, SlfBox)
    assert actual.bottom_right_corner().latitude() == 1
    assert actual.bottom_right_corner().longitude() == 2
    assert actual.top_left_corner().latitude() == 3
    assert actual.top_left_corner().longitude() == 4


def test_parse_unknown_location_type():
    actual = from_location_attribute('geo:???', ['1, 2', '3,4'])
    assert actual is None


def test_parse_unsupported_location_value():
    actual = from_location_attribute('geo:line',
                                     {'start': '1, 2', 'end': '3,4'})
    assert actual is None


def test_parse_invalid_location_value():
    actual = from_location_attribute('geo:line', ['1, 2', '3, wrong!'])
    assert actual is None


def test_parse_empty_location_value():
    actual = from_location_attribute('geo:line', [])
    assert actual is None


def test_parse_empty_location_coords():
    actual = from_location_attribute('geo:line', ['', '1,2'])
    assert actual is None


def test_parse_geojson_location():
    actual = from_location_attribute(
        'geo:json',
        {
            'type': 'Point',
            'coordinates': [2.186447514, 41.3763726]
        })

    assert actual is None


@pytest.mark.parametrize('location', [
    {
        'type': 'geo:point',
        'value': '1.2, -3.045'
    },
    {
        'type': 'geo:line',
        'value': ['1.2, -3.045', '-2.0, 100.0']
    },
    {
        'type': 'geo:polygon',
        'value': ['1.2, -3.045', '-2.0, 100.0', '0.0, 100.0', '2.0005, 100.1',
                  '1.2, -3.045']
    },
    {
        'type': 'geo:box',
        'value': ['1.2, -3.045', '-2.0, 100.0']
    },
])
def test_parse_followed_by_to_attr_is_identity(location):
    parsed = from_location_attribute(location['type'], location['value'])

    assert parsed is not None
    assert location == parsed.to_ngsi_attribute()
