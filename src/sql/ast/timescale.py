from enum import Enum

from geocoding.slf import SlfGeometry, SlfPoint
from .crate import geo_shape_term
from .terms import Term


class GeoIncidenceType(Enum):
    EQUAL = 'ST_Equals'
    DISJOINT = 'ST_Disjoint'
    INTERSECTS = 'ST_Intersects'
    WITHIN = 'ST_Within'


class GeoIncidenceTerm(Term):

    def __init__(self,
                 column_name: str,
                 incidence_type: GeoIncidenceType,
                 geometry: SlfGeometry):
        self.incidence_fn = incidence_type.value
        self.column_name = column_name
        self.geometry = geometry

    def eval(self):
        geo_shape = geo_shape_term(self.geometry)
        return f"{self.incidence_fn}({self.column_name}, {geo_shape})"


class GeoDistanceTerm(Term):

    def __init__(self, column_name: str, point_from: SlfPoint, dist: float):
        self.column_name = column_name
        self.point_from = point_from
        self.dist = dist

    def eval(self):
        pt_from = geo_shape_term(self.point_from)
        dist_rep = f"{self.dist:.16f}".rstrip('0').rstrip('.')
        return f"ST_DWithin({self.column_name}, {pt_from}, {dist_rep})"


def equals(column: str, geometry: SlfGeometry) -> GeoIncidenceTerm:
    return GeoIncidenceTerm(column, GeoIncidenceType.EQUAL, geometry)


def disjoint(column: str, geometry: SlfGeometry) -> GeoIncidenceTerm:
    return GeoIncidenceTerm(column, GeoIncidenceType.DISJOINT, geometry)


def intersects(column: str, geometry: SlfGeometry) -> GeoIncidenceTerm:
    return GeoIncidenceTerm(column, GeoIncidenceType.INTERSECTS, geometry)


def within(column: str, geometry: SlfGeometry) -> GeoIncidenceTerm:
    return GeoIncidenceTerm(column, GeoIncidenceType.WITHIN, geometry)


def distance(column: str, point_from: SlfPoint, dist: float) -> GeoDistanceTerm:
    return GeoDistanceTerm(column, point_from, dist)
