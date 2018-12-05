"""
This module provides functions to convert a Simple Location Format geometry
to GeoJSON. The only function you're likely to need is the ``encode`` function
which serialises an SLF geometry to a GeoJSON string. The other functions
translate SLF geometries to geometry types from the ``geojson`` library.
"""

from typing import Optional
from geojson import dumps, LineString, Point, Polygon
from .geotypes import *


def list_point_tuples(geom: SlfGeometry):
    ps = map(tuple, geom.enum_points())
    return list(ps)


def point_to_json_rep(point: SlfPoint) -> Point:
    p = list_point_tuples(point)[0]
    return Point(p)


def line_to_json_rep(line: SlfLine) -> LineString:
    ps = list_point_tuples(line)
    return LineString(ps)


def polygon_to_json_rep(polygon: SlfPolygon) -> Polygon:
    ps = list_point_tuples(polygon)
    return Polygon(ps)


def box_to_json_rep(box: SlfBox) -> Polygon:
    ps = list_point_tuples(box.to_polygon())
    return Polygon(ps)


def lookup_encoder(geom: SlfGeometry):
    if isinstance(geom, SlfPoint):
        return point_to_json_rep
    if isinstance(geom, SlfLine):
        return line_to_json_rep
    if isinstance(geom, SlfPolygon):
        return polygon_to_json_rep
    if isinstance(geom, SlfBox):
        return box_to_json_rep

    return lambda _: None  # unknown type encoder
# gosh, I wish there were algebraic data types in Python...


def encode(geom: SlfGeometry) -> Optional[str]:
    """
    Convert the given Simple Location Format shape to the corresponding
    GeoJSON shape.

    :param geom: the Simple Location Format shape to convert.
    :return: the GeoJSON as a string if the input shape is of a known type;
        ``None`` otherwise.
    """
    geo_json_rep = lookup_encoder(geom)(geom)
    if geo_json_rep:
        return dumps(geo_json_rep, sort_keys=True)
    return None
