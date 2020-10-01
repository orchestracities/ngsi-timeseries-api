import json
import pytest

from geocoding.slf.geotypes import *
from geocoding.slf.jsoncodec import decode, encode


def test_encode_none_yields_none():
    assert encode(None) is None


@pytest.mark.parametrize('ngsi_type', [
    SlfPoint.ngsi_type(), SlfLine.ngsi_type(), SlfPolygon.ngsi_type(),
    SlfBox.ngsi_type()
])
def test_decode_none_yields_none(ngsi_type):
    assert decode(None, ngsi_type) is None


def test_unknown_geom_yields_none():
    class UnknownGeom(SlfGeometry):
        pass

    assert encode(UnknownGeom()) is None


def test_point():
    pt = SlfPoint(2, 1)
    geoj_pt = {
        'type': 'Point',
        'coordinates': [1, 2]
    }

    json_str = encode(pt)
    assert json_str is not None
    assert json.loads(json_str) == geoj_pt

    decoded_pt = decode(geoj_pt, SlfPoint.ngsi_type())
    assert isinstance(decoded_pt, SlfPoint)
    assert decoded_pt.to_ngsi_attribute() == pt.to_ngsi_attribute()


def test_line():
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    line = SlfLine(points)
    geoj_line = {
        'type': 'LineString',
        'coordinates': [[2, 1], [4, 3]]
    }

    json_str = encode(line)
    assert json_str is not None
    assert json.loads(json_str) == geoj_line

    decoded_line = decode(geoj_line, SlfLine.ngsi_type())
    assert isinstance(decoded_line, SlfLine)
    expected_line = SlfLine(points)  # encode consumed pts stream, need new obj
    assert decoded_line.to_ngsi_attribute() == expected_line.to_ngsi_attribute()


def test_polygon():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(0, -1), SlfPoint(1, 2)]
    polygon = SlfPolygon(points)
    geoj_polygon = {
        'type': 'Polygon',
        'coordinates': [[[2, 1], [4, 3], [-1, 0], [2, 1]]]
    }

    json_str = encode(polygon)
    assert json_str is not None
    assert json.loads(json_str) == geoj_polygon

    decoded_polygon = decode(geoj_polygon, SlfPolygon.ngsi_type())
    assert isinstance(decoded_polygon, SlfPolygon)
    # encode consumed pts stream, need new SLF polygon
    expected_polygon = SlfPolygon(points)
    assert decoded_polygon.to_ngsi_attribute() == \
        expected_polygon.to_ngsi_attribute()


def test_box():
    brc = SlfPoint(0, 1)
    tlc = SlfPoint(1, 0)
    box = SlfBox([brc, tlc])
    geoj_polygon = {
        'type': 'Polygon',
        'coordinates': [[[0, 1], [1, 1], [1, 0], [0, 0], [0, 1]]]
    }

    json_str = encode(box)
    assert json_str is not None
    assert json.loads(json_str) == geoj_polygon

    decoded_box = decode(geoj_polygon, SlfBox.ngsi_type())
    assert isinstance(decoded_box, SlfBox)
    # encode consumed pts stream, need new SLF box
    expected_box = SlfBox([brc, tlc])
    assert decoded_box.to_ngsi_attribute() == expected_box.to_ngsi_attribute()
