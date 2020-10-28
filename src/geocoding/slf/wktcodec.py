"""
This module provides functions to convert a Simple Location Format geometry
to WKT. The only function you're likely to need is the ``encode_as_wkt``
function which serialises an SLF geometry to a WKT string.
"""

from .geotypes import *


def to_wkt_coords(point: SlfPoint) -> str:
    return '{} {}'.format(point.longitude(), point.latitude())


def to_wkt_coords_list(points: Iterable[SlfPoint]) -> str:
    ps = map(to_wkt_coords, points)
    return ', '.join(ps)


def to_wkt_format_string(geom: SlfGeometry) -> Optional[str]:
    if isinstance(geom, SlfPoint):
        return 'POINT ({})'
    if isinstance(geom, SlfLine):
        return 'LINESTRING ({})'
    if isinstance(geom, SlfPolygon):
        return 'POLYGON (({}))'

    return None


def encode_as_wkt(geom: SlfGeometry, srid: Optional[int] = None) \
        -> Optional[str]:
    """
    Convert the given Simple Location Format shape to the corresponding
    WKT shape.

    :param geom: the Simple Location Format shape to convert.
    :param srid: optional spatial reference system ID to include in the shape
        metadata. If given, prepend ``SRID=srid;`` to the WKT string. Notice
        that SRID isn't part of the WKT spec, but is an additional feature
        specified by OpenGIS. Keep this in mind when adding a SRID!
    :return: the WKT string if the input shape is of a known type;
        ``None`` otherwise.
    """
    if isinstance(geom, SlfBox):
        geom = geom.to_polygon()

    ps = to_wkt_coords_list(geom._points())
    str_rep = to_wkt_format_string(geom)
    if str_rep:
        meta = f"SRID={srid};" if srid is not None else ''
        return meta + str_rep.format(ps)
    return None

# TODO. Use shapely.
# A better option than the above code would be the following which uses the
# shapely lib:
#
# from shapely.geometry import shape
# from .jsoncodec import lookup_encoder
#
# def encode_as_wkt(geom: SlfGeometry) -> Optional[str]:
#    geo_json_rep = lookup_encoder(geom)(geom)
#    if geo_json_rep:
#        return shape(geo_json_rep).wkt
#    return None
#
# This works fine for points and lines, but for some obscure reason breaks
# on polygons:
#
# def test_polygon_as_wkt():
#     points = [SlfPoint(1, 2), SlfPoint(3, 4), SlfPoint(0, -1), SlfPoint(1, 2)]
#     polygon = SlfPolygon(points)
#     expected = 'POLYGON ((2 1, 4 3, -1 0, 2 1))'
#
#     assert expected == encode_as_wkt(polygon)
#
# Running the test gives:
#   TypeError: object of type 'int' has no len()
#   shapely/speedups/_speedups.pyx:319: TypeError
