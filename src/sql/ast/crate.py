from enum import Enum
from geocoding.slf import SlfGeometry, SlfPoint, encode_as_wkt
from .terms import *


class GeoMatchType(Enum):
    DISJOINT = 'disjoint'
    INTERSECTS = 'intersects'
    WITHIN = 'within'


def geo_shape_term(geometry: SlfGeometry) -> str:
    geo_shape = encode_as_wkt(geometry)
    return lit(geo_shape).eval()


class GeoMatchTerm(Term):

    def __init__(self, column_name: str,
                 match_type: GeoMatchType,
                 geometry: SlfGeometry):
        self.column_name = column_name
        self.match_type = match_type
        self.geometry = geometry

    def eval(self):
        return 'match ({}, {}) using {}'.format(
            self.column_name,
            geo_shape_term(self.geometry),
            self.match_type.value
        )


class GeoEqualTerm(Term):

    def __init__(self, column_name: str, geometry: SlfGeometry):
        self.column_name = column_name
        self.geometry = geometry

    def eval(self):
        geo_shape = geo_shape_term(self.geometry)
        return 'match ({}, {}) using {} and within({}, {})'.format(
            self.column_name,
            geo_shape,
            GeoMatchType.WITHIN.value,
            geo_shape,
            self.column_name
        )


class GeoDistanceTerm(Term):

    def __init__(self, column_name: str, point_from: SlfPoint):
        self.column_name = column_name
        self.point_from = point_from

    def eval(self):
        return 'distance({}, {})'.format(
            self.column_name, geo_shape_term(self.point_from))


def intersects(column: str, geometry: SlfGeometry) -> GeoMatchTerm:
    return GeoMatchTerm(column, GeoMatchType.INTERSECTS, geometry)


def disjoint(column: str, geometry: SlfGeometry) -> GeoMatchTerm:
    return GeoMatchTerm(column, GeoMatchType.DISJOINT, geometry)


def within(column: str, geometry: SlfGeometry) -> GeoMatchTerm:
    return GeoMatchTerm(column, GeoMatchType.WITHIN, geometry)


def distance(column: str, point_from: SlfPoint):
    return GeoDistanceTerm(column, point_from)


def equals(column: str, geometry: SlfGeometry) -> GeoEqualTerm:
    return GeoEqualTerm(column, geometry)
