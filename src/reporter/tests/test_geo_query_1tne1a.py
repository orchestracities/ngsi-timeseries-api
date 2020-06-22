from .geo_queries_fixture import *


# select * from ettestdevice where
#   ((distance(location_centroid, 'POINT(1.0001 1.0)') >= 10)
#   and (distance(location_centroid, 'POINT(1.0001 1.0)') <= 20));
@pytest.mark.parametrize("service", services)
def test_near_min_max(service, setup_entities):
    query_params = {
        'georel': 'near;minDistance:10;maxDistance:20',
        'geometry': 'point',
        'coords': '1.0,1.0001'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_2)


# select * from ettestdevice where
#   ((distance(location_centroid, 'POINT(1.0001 1.0)') >= 10);
@pytest.mark.parametrize("service", services)
def test_near_min(service, setup_entities):
    query_params = {
        'georel': 'near;minDistance:10',
        'geometry': 'point',
        'coords': '1.0,1.0001'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_1, entity_2)


# select * from ettestdevice where
#   (distance(location_centroid, 'POINT(1.0001 1.0)') <= 20));
@pytest.mark.parametrize("service", services)
def test_near_max(service, setup_entities):
    query_params = {
        'georel': 'near;maxDistance:20',
        'geometry': 'point',
        'coords': '1.0,1.0001'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_2)


# select * from ettestdevice
# where match (location,
#   {type='LineString', coordinates=[[0, 0], [2, 0]]}) using within;
@pytest.mark.parametrize("service", services)
def test_covered_by_line(service, setup_entities):
    query_params = {
        'georel': 'coveredBy',
        'geometry': 'line',
        'coords': '0,0;0,2'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_1)


# select * from ettestdevice
# where match (location,
#   {type='Polygon', coordinates=[[[-0.1, -0.1], [2.1, -0.1], [2.1, 1.1],
#        [-0.1, 1.1], [-0.1, -0.1]]]})
#     using within;
@pytest.mark.parametrize("service", services)
def test_covered_by_polygon(service, setup_entities):
    query_params = {
        'georel': 'coveredBy',
        'geometry': 'polygon',
        'coords': '-0.1,-0.1;-0.1,2.1;1.1,2.1;1.1,-0.1;-0.1,-0.1'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_1, entity_2)


# select * from ettestdevice
# where match (location,
#   {type='LineString', coordinates=[[1, 0], [2, 0]]}) using intersects;
@pytest.mark.parametrize("service", services)
def test_intersects_line(service, setup_entities):
    query_params = {
        'georel': 'intersects',
        'geometry': 'line',
        'coords': '0,1;0,2'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_1)


# select * from ettestdevice where
#   match (location, {type='Point', coordinates=[1, 1]}) using intersects
@pytest.mark.parametrize("service", services)
def test_intersects_point(service, setup_entities):
    query_params = {
        'georel': 'intersects',
        'geometry': 'point',
        'coords': '1,1'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_2)


# select * from ettestdevice where
# match (location, {type='Polygon',
#  coordinates=[[[0.1, -0.1], [1, -0.1], [1, 1.1], [0.1, 1.1], [0.1, -0.1]]]})
#     using intersects;
@pytest.mark.parametrize("service", services)
def test_intersects_polygon(service, setup_entities):
    query_params = {
        'georel': 'intersects',
        'geometry': 'polygon',
        'coords': '-0.1,0.1;-0.1,1;1.1,1;1.1,0.1;-0.1,0.1'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_1, entity_2)


# select * from ettestdevice where
# match (location, {type='Polygon',
#  coordinates=[[[3, 0], [4, 0], [4, 1], [3, 1], [3, 0]]]})
#     using disjoint;
@pytest.mark.parametrize("service", services)
def test_disjoint_with_disjoint_polygon(service, setup_entities):
    query_params = {
        'georel': 'disjoint',
        'geometry': 'polygon',
        'coords': '0,3;0,4;1,4;1,3;0,3'
    }

    r = query_1tne1a(service, query_params)
    assert eids_from_response(r) == expected_eids(entity_1, entity_2)


# select * from ettestdevice where
# match (location, {type='Polygon',
#  coordinates=[[[0.1, -0.1], [1, -0.1], [1, 1.1], [0.1, 1.1], [0.1, -0.1]]]})
#     using disjoint;
@pytest.mark.parametrize("service", services)
def test_disjoint_with_overlapping_polygon(service, setup_entities):
    query_params = {
        'georel': 'disjoint',
        'geometry': 'polygon',
        'coords': '-0.1,0.1;-0.1,1;1.1,1;1.1,0.1;-0.1,0.1'
    }

    query_1tne1a(service, query_params, expected_status_code=404)


@pytest.mark.parametrize("service", services)
def test_equals_not_supported(service, setup_entities):
    query_params = {
        'georel': 'equals',
        'geometry': 'polygon',
        'coords': '-0.1,0.1;-0.1,1;1.1,1;1.1,0.1;-0.1,0.1'
    }

    query_1tne1a(service, query_params, expected_status_code=422)


@pytest.mark.parametrize("service", services)
def test_invalid_geo_params(service, setup_entities):
    query_params = {
        'georel': 'disjoint',
        'coords': '-0.1,0.1;-0.1,1;1.1,1;1.1,0.1;-0.1,0.1'
    }

    query_1tne1a(service, query_params, expected_status_code=400)
