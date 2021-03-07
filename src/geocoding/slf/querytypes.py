"""
This module provides types to represent NGSI geographical query terms.
"""


from typing import Optional
from .geotypes import SlfGeometry, SlfPoint


class SlfQuery:
    """
    Represents an NGSI geographical query whose terms are expressed in the
    Simple Location Format.
    """
    pass


class NearQuery(SlfQuery):
    """
    Represents the near query, i.e. a query having ``georel=near``.
    """

    def __init__(self,
                 geometry: SlfGeometry,
                 min_distance: Optional[float],
                 max_distance: Optional[float]):
        self._centroid = geometry.centroid2d()
        self._min = min_distance
        self._max = max_distance

    def centroid(self) -> Optional[SlfPoint]:
        return self._centroid

    def min_distance(self) -> Optional[float]:
        return self._min

    def max_distance(self) -> Optional[float]:
        return self._max

    @staticmethod
    def georel_type():
        return 'near'

    @staticmethod
    def min_distance_key():
        return 'minDistance'

    @staticmethod
    def max_distance_key():
        return 'maxDistance'


class ShapeQuery(SlfQuery):
    """
    Factors out functionality shared by all queries that involve determining
    in which relationship two shapes stand.
    """

    def __init__(self, geometry: SlfGeometry):
        self._reference_shape = geometry

    def reference_shape(self) -> SlfGeometry:
        return self._reference_shape


class CoveredByQuery(ShapeQuery):
    """
    Represents the covered-by query, i.e. a query having ``georel=coveredBy``.
    """
    @staticmethod
    def georel_type():
        return 'coveredBy'


class IntersectsQuery(ShapeQuery):
    """
    Represents the intersects query, i.e. a query having ``georel=intersects``.
    """
    @staticmethod
    def georel_type():
        return 'intersects'


class EqualsQuery(ShapeQuery):
    """
    Represents the equals query, i.e. a query having ``georel=equals``.
    """
    @staticmethod
    def georel_type():
        return 'equals'


class DisjointQuery(ShapeQuery):
    """
    Represents the disjoint query, i.e. a query having ``georel=disjoint``.
    """
    @staticmethod
    def georel_type():
        return 'disjoint'
