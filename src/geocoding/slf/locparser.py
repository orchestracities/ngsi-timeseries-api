"""
This module provides the functionality to convert dictionary representations of
Simple Location Format geometries to instances of the data types from the
``geotypes`` module. The only function you're likely to ever need is
``from_location_attribute`` which extracts the content of an NGSI entity's
location attribute and instantiates an ``SlfGeometry`` with that data as long
as the location attribute contains Simple Location Format data.
"""


from typing import Optional
from .geotypes import *


# NOTE. Consider using parser combinators instead of the below poor man's
# approach to parsing.


def point_from_wgs84(string_rep: str) -> SlfPoint:
    """
    Parse WGS84 coordinates into an ``SlfPoint``.
    :param string_rep: a WGS84 representation of a latitude/longitude pair,
        i.e. a string in the format "lat, lon".
    :return: a new ``SlfPoint`` with the specified latitude and longitude.
    :raise TypeError: if the argument is ``None`` or isn't a string.
    :raise ValueError: if the coordinates aren't two decimal numbers
        separated by a comma.
    """
    if string_rep is not None and isinstance(string_rep, str):
        lat, lon = string_rep.split(',')
        return SlfPoint(float(lat), float(lon))
    raise TypeError


def points_from_wgs84(ps: Iterable[str]) -> Iterable[SlfPoint]:
    """
    Map ``SlfPoint.from_wgs84`` over the input iterable of WGS84 points.
    :param ps: the points.
    :return: a list of ``SlfPoint``s.
    :raise TypeError: if the argument is ``None``.
    """
    for p in ps:
        yield point_from_wgs84(p)


def location_point_parser(geom: str) -> SlfPoint:
    return point_from_wgs84(geom)


def location_line_parser(geom: Iterable[str]) -> SlfLine:
    points = points_from_wgs84(geom)
    return SlfLine(points)


def location_polygon_parser(geom: Iterable[str]) -> SlfPolygon:
    points = points_from_wgs84(geom)
    return SlfPolygon(points)


def location_box_parser(geom: Iterable[str]) -> SlfBox:
    points = points_from_wgs84(geom)
    return SlfBox(points)


def lookup_parser(ngsi_geom_type: str):
    parsers = {
        SlfPoint.ngsi_type(): location_point_parser,
        SlfLine.ngsi_type(): location_line_parser,
        SlfPolygon.ngsi_type(): location_polygon_parser,
        SlfBox.ngsi_type(): location_box_parser
    }

    def unknown_type_parser(_):
        return None

    return parsers.get(ngsi_geom_type, unknown_type_parser)


def from_location_attribute(entity: dict) -> Optional[SlfGeometry]:
    """
    Convert the entity's location attribute (if any) to the corresponding
    instance of a Simple Location Format type.

    :param entity: an NGSI entity.
    :return: the corresponding Simple Location Format geometry if the entity
        contains a valid location attribute with a Simple Location Format
        geometry; ``None`` otherwise. In particular, return ``None`` if the
        entity already has a location attribute with GeoJSON geometry.
    """
    entity = {} if entity is None else entity
    location = entity.get('location', {})
    geom_type = location.get('type', None)
    geom = location.get('value', None)

    try:
        return lookup_parser(geom_type)(geom)
    except (TypeError, ValueError):
        return None
