"""
This module provides various parsers to transform an NGSI geographical query
string into an AST. The only function you're likely to ever need is
``from_geo_params`` which takes care of orchestrating the parsers to produce
one of the data type instances from the ``querytypes`` module.
"""


import re
from typing import Callable
from .geotypes import *
from .querytypes import *


# NOTE. Parser combinators.
# Using parser combinators would be much cleaner, more concise and easier
# to maintain than the regex mess below. But for the moment...bless this
# mess!


class QueryTypeParser:

    def __init__(self, geometry: SlfGeometry):
        self.geometry = geometry

    def parse(self, georel_value: str) -> Optional[SlfQuery]:
        pattern = self._compile_pattern()
        match = pattern.match(georel_value)
        if match:
            query_ctor = self._extract_terms(match)
            return query_ctor(self.geometry)
        return None

    def _compile_pattern(self):
        pass

    def _extract_terms(self, match) -> Callable[[SlfGeometry], SlfQuery]:
        pass

    @staticmethod
    def _compile_simple_georel_pattern(georel_type: str):
        regex = '^{}$'.format(georel_type)
        return re.compile(regex)

    @staticmethod
    def _compile_near_pattern(distance_key_1, distance_key_2):
        distance_value_regex = '(0|([1-9][0-9]*))([.][0-9]+)?'

        if distance_key_1 and distance_key_2:
            regex = '^{};{}:({});{}:({})$'.format(
                NearQuery.georel_type(),
                distance_key_1, distance_value_regex,
                distance_key_2, distance_value_regex)
        else:
            dkey = distance_key_1 if distance_key_1 else distance_key_2
            regex = '^{};{}:({})$'.format(
                NearQuery.georel_type(),
                dkey, distance_value_regex)

        return re.compile(regex)


class CoveredByParser(QueryTypeParser):

    def _compile_pattern(self):
        qtype = CoveredByQuery.georel_type()
        return self._compile_simple_georel_pattern(qtype)

    def _extract_terms(self, match):
        return CoveredByQuery


class IntersectsParser(QueryTypeParser):

    def _compile_pattern(self):
        qtype = IntersectsQuery.georel_type()
        return self._compile_simple_georel_pattern(qtype)

    def _extract_terms(self, match):
        return IntersectsQuery


class DisjointParser(QueryTypeParser):

    def _compile_pattern(self):
        qtype = DisjointQuery.georel_type()
        return self._compile_simple_georel_pattern(qtype)

    def _extract_terms(self, match):
        return DisjointQuery


class EqualsParser(QueryTypeParser):

    def _compile_pattern(self):
        qtype = EqualsQuery.georel_type()
        return self._compile_simple_georel_pattern(qtype)

    def _extract_terms(self, match):
        return EqualsQuery


class NearMinMaxParser(QueryTypeParser):

    def _compile_pattern(self):
        return self._compile_near_pattern(
            NearQuery.min_distance_key(), NearQuery.max_distance_key()
        )

    def _extract_terms(self, match):
        min_d = float(match.group(1))
        max_d = float(match.group(5))
        return lambda geom: NearQuery(geom, min_d, max_d)


class NearMaxMinParser(QueryTypeParser):

    def _compile_pattern(self):
        return self._compile_near_pattern(
            NearQuery.max_distance_key(), NearQuery.min_distance_key()
        )

    def _extract_terms(self, match):
        max_d = float(match.group(1))
        min_d = float(match.group(5))
        return lambda geom: NearQuery(geom, min_d, max_d)


class NearMinParser(QueryTypeParser):

    def _compile_pattern(self):
        return self._compile_near_pattern(NearQuery.min_distance_key(), None)

    def _extract_terms(self, match):
        min_d = float(match.group(1))
        return lambda geom: NearQuery(geom, min_d, None)


class NearMaxParser(QueryTypeParser):

    def _compile_pattern(self):
        return self._compile_near_pattern(NearQuery.max_distance_key(), None)

    def _extract_terms(self, match):
        max_d = float(match.group(1))
        return lambda geom: NearQuery(geom, None, max_d)


class CoordsParser:

    def parse(self, coords: str) -> Optional[Iterable[SlfPoint]]:
        match = self.pattern().match(coords)
        if match:
            ps = coords.split(';')
            return self.parse_points(ps)
        return None

    @staticmethod
    def parse_points(ps: Iterable[str]) -> Iterable[SlfPoint]:
        for p in ps:
            yield CoordsParser.parse_point(p)

    @staticmethod
    def parse_point(pt: str) -> SlfPoint:
        lat_lon = pt.split(',')
        lat = float(lat_lon[0])
        lon = float(lat_lon[1])
        return SlfPoint(lat, lon)

    @staticmethod
    def pattern():
        float_regex = '[+,-]?(0|([1-9][0-9]*))([.][0-9]+)?'
        regex = '^{},{}(;{},{})*$'.format(
            float_regex, float_regex, float_regex, float_regex)
        return re.compile(regex)


class GeometryParser:

    def parse(self, geometry_type: str, coords: str) -> Optional[SlfGeometry]:
        points = CoordsParser().parse(coords)
        builder = self.lookup_geom_builder(geometry_type)
        if points and builder:
            return builder(points)
        return None

    @staticmethod
    def lookup_geom_builder(geometry_type: str)\
            -> Callable[[Iterable[SlfPoint]], SlfGeometry]:
        type_to_builder = {
            'point': lambda ps: next(iter(ps)),
            'line': SlfLine,
            'polygon': SlfPolygon,
            'box': SlfBox
        }
        return type_to_builder.get(geometry_type)


def from_geo_params(georel: Optional[str],
                    geometry: Optional[str],
                    coords: Optional[str]) -> Optional[SlfQuery]:
    """
    Parse a Simple Location Format geographical query string into the
    corresponding data type.

    :param georel: the value of the ``georel`` query parameter.
    :param geometry: the value of the ``geometry`` query parameter.
    :param coords: the value of the ``coords`` query parameter.
    :return: ``None`` if all input arguments are ``None``, otherwise an instance
        of a query type to represent the input data.
    :raise ValueError: if the arguments don't represent a valid query.
    """
    if (georel, geometry, coords) == (None, None, None):
        return None

    if georel and geometry and coords:
        geom = GeometryParser().parse(geometry, coords)
        if geom:
            query_type_parsers = [
                IntersectsParser,
                DisjointParser,
                EqualsParser,
                CoveredByParser,
                NearMinMaxParser,
                NearMaxMinParser,
                NearMinParser,
                NearMaxParser]
            for p in query_type_parsers:
                query = p(geom).parse(georel)
                if query:
                    return query

    raise ValueError
