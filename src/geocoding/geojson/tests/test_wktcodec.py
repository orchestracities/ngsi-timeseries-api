from geocoding.geojson.wktcodec import *
import pytest

# NOTE. GeoJSON below comes from: https://en.wikipedia.org/wiki/GeoJSON

geoj_point = {
    'type': 'Point',
    'coordinates': [30, 10]
}

wkt_point = 'POINT (30 10)'

geoj_linestring = {
    'type': 'LineString',
    'coordinates': [
        [30, 10], [10, 30], [40, 40]
    ]
}
wkt_linestring = 'LINESTRING (30 10, 10 30, 40 40)'

geoj_polygon = {
    'type': 'Polygon',
    'coordinates': [
        [[30, 10], [40, 40], [20, 40], [10, 20], [30, 10]]
    ]
}

wkt_polygon = 'POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))'

geoj_polygon_with_hole = {
    'type': 'Polygon',
    'coordinates': [
        [[35, 10], [45, 45], [15, 40], [10, 20], [35, 10]],
        [[20, 30], [35, 35], [30, 20], [20, 30]]
    ]
}

wkt_polygon_with_hole = 'POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10), ' + \
                        '(20 30, 35 35, 30 20, 20 30))'

geoj_geom_collection = {
    'type': 'GeometryCollection',
    'geometries': [
        {
            'type': 'Point',
            'coordinates': [40, 10]
        },
        {
            'type': 'LineString',
            'coordinates': [
                [10, 10], [20, 20], [10, 40]
            ]
        },
        {
            'type': 'Polygon',
            'coordinates': [
                [[40, 40], [20, 45], [45, 30], [40, 40]]
            ]
        }
    ]
}

wkt_geom_collection = 'GEOMETRYCOLLECTION (POINT (40 10),' + \
                      'LINESTRING (10 10, 20 20, 10 40),' + \
                      'POLYGON ((40 40, 20 45, 45 30, 40 40)))'


@pytest.mark.parametrize('input_geoj, expected_wkt', [
    (geoj_point, wkt_point),
    (geoj_linestring, wkt_linestring),
    (geoj_polygon, wkt_polygon),
    (geoj_polygon_with_hole, wkt_polygon_with_hole),
    (geoj_geom_collection, wkt_geom_collection)
])
def test_encode_as_wkt(input_geoj, expected_wkt):
    assert encode_as_wkt(input_geoj, decimals=0) == expected_wkt


@pytest.mark.parametrize('input_geoj', [
    geoj_point, geoj_linestring, geoj_polygon, geoj_polygon_with_hole,
    geoj_geom_collection
])
def test_encode_as_wkt_then_decode(input_geoj):
    wkt_str = encode_as_wkt(input_geoj)
    decoded_geoj = decode_wkt(wkt_str)
    assert decoded_geoj == input_geoj


@pytest.mark.parametrize('input_geoj', [
    geoj_point, geoj_linestring, geoj_polygon, geoj_polygon_with_hole,
    geoj_geom_collection
])
def test_encode_as_wkb_then_decode(input_geoj):
    wkb_bytes = encode_as_wkb(input_geoj)
    decoded_geoj = decode_wkb(wkb_bytes)
    assert decoded_geoj == input_geoj


@pytest.mark.parametrize('input_geoj', [
    geoj_point, geoj_linestring, geoj_polygon, geoj_polygon_with_hole,
    geoj_geom_collection
])
def test_encode_as_wkb_hex_then_decode(input_geoj):
    wkb_hex = encode_as_wkb_hex(input_geoj)
    decoded_geoj = decode_wkb_hexstr(wkb_hex)
    assert decoded_geoj == input_geoj
