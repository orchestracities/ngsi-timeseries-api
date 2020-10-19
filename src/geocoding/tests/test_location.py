import pytest
from geocoding.location import *


@pytest.mark.parametrize('entity', [
    None, {}
])
def test_loc_attr_with_no_data(entity):
    target = LocationAttribute(entity)
    assert target.geometry_type() is None
    assert target.geometry_value() is None


@pytest.mark.parametrize('entity, expected', [
    (None, None), ({}, {}), ({'location': {}}, {'location': {}}),
    ({'location': {'type': ''}}, {'location': {'type': ''}}),
    ({'location': {'type': 'geo:line'}}, {'location': {'type': 'geo:line'}})
])
def test_normalize_noop_when_invalid_input_and_no_existing_centroid(entity,
                                                                    expected):
    normalize_location(entity)
    assert entity == expected


@pytest.mark.parametrize('entity, expected', [
    ({'location_centroid': [1, 2]}, {}),
    ({'location': {}, 'location_centroid': [1, 2]}, {'location': {}}),
    ({'location': {'type': ''}, 'location_centroid': [1, 2]},
     {'location': {'type': ''}}),
    ({'location': {'type': 'geo:line'}, 'location_centroid': [1, 2]},
     {'location': {'type': 'geo:line'}})
])
def test_normalize_remove_centroid(entity, expected):
    normalize_location(entity)
    assert entity == expected


@pytest.mark.parametrize('entity', [
    {
        'location': {
            'type': 'geo:json',
            'value': {
                'type': 'Point',
                'coordinates': [2, 1]
            }
        }
    },
    {
        'location': {
            'type': 'geo:json',
            'value': {
                'type': 'Point',
                'coordinates': [2, 1]
            }
        },
        'location_centroid': [5, 9]
    }
])
def test_normalize_leave_json_be_but_add_or_update_centroid(entity):
    normalize_location(entity)

    assert entity['location'] == {
        'type': 'geo:json',
        'value': {
            'type': 'Point',
            'coordinates': [2, 1]
        }
    }

    assert entity['location_centroid'] == {
        'type': 'geo:point',
        'value': '1.0, 2.0'
    }


@pytest.mark.parametrize('entity', [
    {
        'location': {'type': 'geo:point', 'value': '1, 2'}
    },
    {
        'location': {'type': 'geo:point', 'value': '1, 2'},
        'location_centroid': [5, 9]
    }
])
def test_normalize_get_json_point_and_add_or_update_centroid(entity):
    normalize_location(entity)

    assert entity['location'] == {
        'type': 'geo:json',
        'value': {
            'type': 'Point',
            'coordinates': [2, 1]
        }
    }

    assert entity['location_centroid'] == {
        'type': 'geo:point',
        'value': '1.0, 2.0'
    }


@pytest.mark.parametrize('entity', [
    {
        'location': {'type': 'geo:line', 'value': ['1,2', '1,4']}
    },
    {
        'location': {'type': 'geo:line', 'value': ['1,2', '1,4']},
        'location_centroid': [5, 9]
    }
])
def test_normalize_get_json_line_and_add_or_update_centroid(entity):
    normalize_location(entity)

    assert entity['location'] == {
        'type': 'geo:json',
        'value': {
            'type': 'LineString',
            'coordinates': [[2, 1], [4, 1]]
        }
    }

    assert entity['location_centroid'] == {
        'type': 'geo:point',
        'value': '1.0, 3.0'
    }


@pytest.mark.parametrize('entity', [
    {
        'location': {
            'type': 'geo:polygon',
            'value': ['1,2', '1,4', '-1,4', '-1,2']
        }
    },
    {
        'location': {
            'type': 'geo:polygon',
            'value': ['1,2', '1,4', '-1,4', '-1,2']
        },
        'location_centroid': [5, 9]
    }
])
def test_normalize_get_json_polygon_and_add_or_update_centroid(entity):
    normalize_location(entity)

    assert entity['location'] == {
        'type': 'geo:json',
        'value': {
            'type': 'Polygon',
            'coordinates': [[[2, 1], [4, 1], [4, -1], [2, -1]]]
        }
    }

    assert entity['location_centroid'] == {
        'type': 'geo:point',
        'value': '0.0, 3.0'
    }


@pytest.mark.parametrize('entity', [
    {
        'location': {'type': 'geo:box', 'value': ['-1,4', '1,2']}
    },
    {
        'location': {'type': 'geo:box', 'value': ['-1,4', '1,2']},
        'location_centroid': [5, 9]
    }
])
def test_normalize_get_json_from_box_and_add_or_update_centroid(entity):
    normalize_location(entity)

    assert entity['location'] == {
        'type': 'geo:json',
        'value': {
            'type': 'Polygon',
            'coordinates': [[[2, 1], [4, 1], [4, -1], [2, -1], [2, 1]]]
        }
    }

    assert entity['location_centroid'] == {
        'type': 'geo:point',
        'value': '0.0, 3.0'
    }
