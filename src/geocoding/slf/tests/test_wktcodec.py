from geocoding.slf import *


def test_point():
    pt = SlfPoint(2, 1)
    expected = 'POINT (1 2)'

    assert expected == encode_as_wkt(pt)


def test_line():
    points = [SlfPoint(1, 2), SlfPoint(3, 4)]
    line = SlfLine(points)
    expected = 'LINESTRING (2 1, 4 3)'

    assert expected == encode_as_wkt(line)


def test_polygon():
    points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(0, -1), SlfPoint(1, 2)]
    polygon = SlfPolygon(points)
    expected = 'POLYGON ((2 1, 4 3, -1 0, 2 1))'

    assert expected == encode_as_wkt(polygon)


def test_box():
    brc = SlfPoint(0, 1)
    tlc = SlfPoint(1, 0)
    box = SlfBox([brc, tlc])
    expected = 'POLYGON ((0 1, 1 1, 1 0, 0 0, 0 1))'

    assert expected == encode_as_wkt(box)
