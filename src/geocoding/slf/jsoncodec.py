"""
This module provides functions to convert a Simple Location Format geometry
to GeoJSON and back. The only functions you're likely to need are the ``encode``
function which serialises an SLF geometry to a GeoJSON string and the ``decode``
function which converts GeoJSON to SLF. The other functions translate SLF
geometries to geometry types from the ``geojson`` library and from GeoJSON
to SLF.
"""

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
    return Polygon([ps])


def box_to_json_rep(box: SlfBox) -> Polygon:
    ps = list_point_tuples(box.to_polygon())
    return Polygon([ps])


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


def geo_type(geo_json: dict) -> Optional[str]:
    return maybe_value(geo_json, 'type')


def geo_coords(geo_json: dict) -> Optional[List]:
    return maybe_value(geo_json, 'coordinates')


def point_from_geo_coords(xyz: [float]) -> SlfPoint:
    return SlfPoint(longitude=xyz[0], latitude=xyz[1])


def geo_point_to_point(geo_json: dict) -> Optional[SlfPoint]:
    coords = geo_coords(geo_json)
    if geo_type(geo_json) == 'Point' and coords:
        return point_from_geo_coords(coords)
    return None


def geo_linestring_to_line(geo_json: dict) -> Optional[SlfLine]:
    coords = geo_coords(geo_json)
    if geo_type(geo_json) == 'LineString' and coords:
        ps = [point_from_geo_coords(xyz) for xyz in coords]
        return SlfLine(ps)
    return None


def geo_polygon_to_polygon(geo_json: dict) -> Optional[SlfPolygon]:
    coords = geo_coords(geo_json)
    if geo_type(geo_json) == 'Polygon' and coords:
        linear_ring = coords[0]  # see RFC 7946 § 3.1.6
        ps = [point_from_geo_coords(xyz) for xyz in linear_ring]
        return SlfPolygon(ps)
    return None


def geo_polygon_to_box(geo_json: dict) -> Optional[SlfBox]:
    coords = geo_coords(geo_json)
    if geo_type(geo_json) == 'Polygon' and coords:
        linear_ring = coords[0]  # see RFC 7946 § 3.1.6
        bottom_right_corner = linear_ring[2]  # see SlfBox.to_polygon
        top_left_corner = linear_ring[0]
        ps = [point_from_geo_coords(bottom_right_corner),
              point_from_geo_coords(top_left_corner)]
        return SlfBox(ps)
    return None


def decode(geo_json: dict, ngsi_type: str) -> Optional[SlfGeometry]:
    """
    Convert the given GeoJSON geometry to a Simple Location Format shape.

    :param geo_json: the GeoJSON geometry to convert.
    :param ngsi_type: the desired output type.
    :return: the SLF geometry object corresponding to the input GeoJSON if
        its geometry type can be converted to given NGSI SLF type; ``None``
        otherwise.
    """
    converters = {
        SlfPoint.ngsi_type(): geo_point_to_point,
        SlfLine.ngsi_type(): geo_linestring_to_line,
        SlfPolygon.ngsi_type(): geo_polygon_to_polygon,
        SlfBox.ngsi_type(): geo_polygon_to_box
    }
    converter = converters.get(ngsi_type, None)
    if converter:
        return converter(geo_json)
    return None
