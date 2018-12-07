import pytest
from geocoding.slf.queryparser import *


@pytest.mark.parametrize('parser_class, query_class', [
    (EqualsParser, EqualsQuery), (IntersectsParser, IntersectsQuery),
    (DisjointParser, DisjointQuery), (CoveredByParser, CoveredByQuery)
])
def test_simple_query_parser(parser_class, query_class):
    geometry = SlfPoint(1, 2)
    parser = parser_class(geometry)
    query = parser.parse(query_class.georel_type())

    assert query is not None
    assert isinstance(query, query_class)
    assert query.reference_shape() is not None


@pytest.mark.parametrize('parser_class, georel_value', [
    (NearMinMaxParser, 'near;minDistance:1.2;maxDistance:3.4'),
    (NearMaxMinParser, 'near;maxDistance:3.4;minDistance:1.2'),
    (NearMinParser, 'near;minDistance:1.2'),
    (NearMaxParser, 'near;maxDistance:3.4')
])
def test_near_parser(parser_class, georel_value):
    geometry = SlfPoint(1, 2)
    parser = parser_class(geometry)
    query = parser.parse(georel_value)

    assert query is not None
    assert isinstance(query, NearQuery)
    assert query.centroid() is not None
    assert query.centroid().longitude() == geometry.longitude()
    assert query.centroid().latitude() == geometry.latitude()
    if 'min' in georel_value:
        assert query.min_distance() == 1.2
    else:
        assert query.min_distance() is None
    if 'max' in georel_value:
        assert query.max_distance() == 3.4
    else:
        assert query.max_distance() is None


@pytest.mark.parametrize('coords', [
    '', ' ', '+,', '-;', '1,2,3,4', '+ 1, 2',
    '1, 2', '1, 2; 3,4', '1, 2; 3, 4',
    '1,2 ', '1,2; 3,4', '1,2;3,4;'
])
def test_coords_parser_return_none_if_invalid_format(coords):
    assert CoordsParser().parse(coords) is None


@pytest.mark.parametrize('coords', [
    '1.2,3', '+1.2,+3', '1.2,+3'
])
def test_coords_parser_one_point(coords):
    parsed = CoordsParser().parse(coords)
    ps = list(parsed)

    assert len(ps) == 1
    assert ps[0].latitude() == 1.2
    assert ps[0].longitude() == 3


@pytest.mark.parametrize('coords', [
    '1.2,3;-4,-5.6', '+1.2,+3;-4,-5.6', '1.2,+3;-4,-5.6'
])
def test_coords_parser_many_points(coords):
    parsed = CoordsParser().parse(coords)
    ps = list(parsed)

    assert len(ps) == 2
    assert ps[0].latitude() == 1.2
    assert ps[0].longitude() == 3
    assert ps[1].latitude() == -4
    assert ps[1].longitude() == -5.6


def test_from_geo_params_return_none_no_args():
    assert from_geo_params(None, None, None) is None


@pytest.mark.parametrize('georel, geom, coords', [
    ('', None, None), (None, '', None), (None, None, ''),
    ('', '', None), ('', None, ''), (None, '', ''),
    ('', '', ''),
    ('equals', None, None), (None, 'line', None), (None, None, '1,2'),
    ('equals', 'line', None), ('equals', None, '1,2'), (None, 'line', '1,2')
])
def test_from_geo_params_fail_if_some_args_missing(georel, geom, coords):
    with pytest.raises(ValueError):
        from_geo_params(georel, geom, coords)


@pytest.mark.parametrize('georel, geom, coords', [
    ('equals', '?', None), (None, 'line', None), (None, None, '1,2'),
    ('equals', 'line', None), ('equals', None, '1,2'), (None, 'line', '1,2')
])
def test_from_geo_params_fail_if_invalid_args(georel, geom, coords):
    with pytest.raises(ValueError):
        from_geo_params(georel, geom, coords)


@pytest.mark.parametrize('georel, query_class', [
    ('equals', EqualsQuery), ('intersects', IntersectsQuery),
    ('disjoint', DisjointQuery), ('coveredBy', CoveredByQuery),
    ('near;minDistance:1', NearQuery)
])
def test_from_geo_params_with_polygon(georel, query_class):
    parsed = from_geo_params(georel,
                             geometry='polygon',
                             coords='1,2;3,4;-1,-2;1,2')

    assert parsed is not None
    assert isinstance(parsed, query_class)
