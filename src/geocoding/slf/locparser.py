"""
This module provides the functionality to convert dictionary representations of
Simple Location Format geometries to instances of the data types from the
``geotypes`` module. The only function you're likely to ever need is
``from_location_attribute`` which instantiates an ``SlfGeometry`` from Simple
Location Format data contained in an NGSI entity's location attribute.
"""


from typing import Optional, Union, List
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


def from_location_attribute(geom_type: Optional[str],
                            geom: Optional[Union[str, List[str], dict]])\
        -> Optional[SlfGeometry]:
    """
    Instantiates an ``SlfGeometry`` from Simple Location Format data.

    :param geom_type: the Simple Location Format geometry type.
    :param geom: a shape of ``geom_type``.
    :return: the corresponding Simple Location Format geometry if the input
        data is a valid Simple Location Format geometry; ``None`` otherwise.
        In particular, return ``None`` in the case of a GeoJSON geometry.
    """
    try:
        return lookup_parser(geom_type)(geom)
    except (TypeError, ValueError):
        return None
