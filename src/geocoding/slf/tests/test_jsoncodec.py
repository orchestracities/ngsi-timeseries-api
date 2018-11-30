import json
from geocoding.slf.geotypes import *
from geocoding.slf.jsoncodec import encode


def test_none_yields_none():
    assert encode(None) is None


def test_unknown_geom_yields_none():
    class UnknownGeom(SlfGeometry):
        pass

    assert encode(UnknownGeom()) is None


def test_point():
    pt = SlfPoint(2, 1)
    expected = {
        'type': 'Point',
        'coordinates': [1, 2]
    }

    json_str = encode(pt)
    assert json_str is not None
    assert expected == json.loads(json_str)


def test_line():
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    line = SlfLine(points)
    expected = {
        'type': 'LineString',
        'coordinates': [[2, 1], [4, 3]]
    }

    json_str = encode(line)
    assert json_str is not None
    assert expected == json.loads(json_str)


def test_polygon():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(0, -1), SlfPoint(1, 2)]
    polygon = SlfPolygon(points)
    expected = {
        'type': 'Polygon',
        'coordinates': [[2, 1], [4, 3], [-1, 0], [2, 1]]
    }

    json_str = encode(polygon)
    assert json_str is not None
    assert expected == json.loads(json_str)


def test_box():
    brc = SlfPoint(0, 1)
    tlc = SlfPoint(1, 0)
    box = SlfBox([brc, tlc])
    expected = {
        'type': 'Polygon',
        'coordinates': [[0, 1], [1, 1], [1, 0], [0, 0]]
    }

    json_str = encode(box)
    assert json_str is not None
    assert expected == json.loads(json_str)
