import pytest
from geocoding.centroid import centroid2d, maybe_centroid2d, geojson_centroid


def test_centroid_of_none_should_fail():
    with pytest.raises(TypeError):
        centroid2d(None)


def test_centroid_of_empty_list_should_fail():
    with pytest.raises(ZeroDivisionError):
        centroid2d([])


def test_centroid_of_missing_coord_should_fail():
    with pytest.raises(TypeError):
        centroid2d([[None, 1], [1, 2]])


def test_centroid_of_missing_coords_should_fail():
    with pytest.raises(IndexError):
        centroid2d([[], [1, 2]])


def test_centroid_of_ill_typed_coord_should_fail():
    with pytest.raises(TypeError):
        centroid2d([[1, 2], [2, '']])


@pytest.mark.parametrize('points', [
    [[0, 0]], [[1, 0]], [[0, 1]], [[2, 2]]
])
def test_centroid_of_point_is_point_itself(points):
    p = points[0]
    assert p == centroid2d(points)


@pytest.mark.parametrize('fixture', [
    ([[0, 0], [2, 0]], [1, 0]),
    ([[1, 1], [3, 3]], [2, 2]),
    ([[1, 2], [2, 4], [3, 6]], [2, 4])
])
def test_centroid_of_list_of_points(fixture):
    points = fixture[0]
    expected = fixture[1]

    assert expected == centroid2d(points)


def test_centroid_of_iterable_of_points():
    def points():
        for p in [[1, 1], [3, 3]]:
            yield p

    assert [2, 2] == centroid2d(points())


@pytest.mark.parametrize('points', [
    None, [], [[]], [[None, 1], [1, 2]], [[1, 2], [2, '']]
])
def test_maybe_centroid_of_bad_inputs_should_return_none(points):
    actual = maybe_centroid2d(points)
    assert actual is None


@pytest.mark.parametrize('points', [
    [[1, 2]],
    [[0, 0], [2, 0]],
    [[1, 1], [3, 3]],
    [[1, 2], [2, 4], [3, 6]]
])
def test_maybe_centroid_of_valid_inputs_same_as_centroid2d(points):
    actual = maybe_centroid2d(points)
    expected = centroid2d(points)
    assert expected == actual


def test_geojson_centroid_of_feature_collection():
    d = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [102.0, 0.5]
                },
                'properties': {
                    'prop0': 'value0'
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [
                        [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]
                    ]
                },
                'properties': {
                    'prop0': 'value0',
                    'prop1': 0.0
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                        [
                            [100.0, 0.0], [101.0, 0.0], [101.0, 1.0],
                            [100.0, 1.0], [100.0, 0.0]
                        ]
                    ]
                },
                'properties': {
                    'prop0': 'value0',
                    'prop1': {'this': 'that'}
                }
            }
        ]
    }

    ps = [
        # point
        [102.0, 0.5],
        # line
        [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0],
        # polygon
        [100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]
    ]
    expected = centroid2d(ps)

    assert expected == geojson_centroid(d)


def test_geojson_centroid_of_multipolygon():
    d = {
        'type': 'MultiPolygon',
        'coordinates': [
            [
                [[30, 20], [45, 40], [10, 40], [30, 20]]
            ],
            [
                [[15, 5], [40, 10], [10, 20], [5, 10], [15, 5]]
            ]
        ]
    }

    ps = [
        [30, 20], [45, 40], [10, 40], [30, 20],        # first polygon
        [15, 5], [40, 10], [10, 20], [5, 10], [15, 5]  # second polygon
    ]
    expected = centroid2d(ps)

    assert expected == geojson_centroid(d)
