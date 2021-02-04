from typing import Optional
from .centroid import geojson_centroid
from .slf import from_location_attribute, SlfPoint
from .slf.jsoncodec import lookup_encoder


LOCATION_ATTR_NAME = 'location'
CENTROID_ATTR_NAME = 'location_centroid'
_TYPE_ATTR_NAME = 'type'
_VALUE_ATTR_NAME = 'value'
_GEOJSON_TYPE = 'geo:json'
_GEOJSON_LD_TYPE = 'GeoProperty'


class LocationAttribute:

    def __init__(self, entity: Optional[dict]):
        entity = {} if entity is None else entity
        self._location = entity.get(LOCATION_ATTR_NAME, {})

    def geometry_type(self) -> Optional[str]:
        return self._location.get(_TYPE_ATTR_NAME, None)

    def geometry_value(self) -> Optional[str]:
        return self._location.get(_VALUE_ATTR_NAME, None)

    def is_geojson(self):
        return self.geometry_type() == _GEOJSON_TYPE or \
            self.geometry_type() == _GEOJSON_LD_TYPE

    def _compute_geojson_centroid(self):
        lon_lat = geojson_centroid(self.geometry_value())
        return SlfPoint(longitude=lon_lat[0], latitude=lon_lat[1]) if lon_lat \
            else None

    def _compute_slf_centroid(self):
        geom = from_location_attribute(self.geometry_type(),
                                       self.geometry_value())
        return geom.centroid2d() if geom else None

    def compute_centroid(self) -> Optional[SlfPoint]:
        if self.is_geojson():
            return self._compute_geojson_centroid()
        return self._compute_slf_centroid()

    def geometry_value_as_geojson(self) -> Optional[dict]:
        if self.is_geojson():
            return self.geometry_value()

        geom = from_location_attribute(self.geometry_type(),
                                       self.geometry_value())
        return lookup_encoder(geom)(geom)

    def as_geojson(self):
        geometry = self.geometry_value_as_geojson()
        if geometry is None:
            return None
        else:
            return {
                _TYPE_ATTR_NAME: _GEOJSON_TYPE,
                _VALUE_ATTR_NAME: geometry
            }


def normalize_location(entity: Optional[dict]):
    """
    Force GeoJSON for the input entity's location attribute and add the location
    centroid attribute to the entity.
    If no entity is passed in or there's no location attribute or the location
    isn't of a known type, this function won't modify or add the location
    attribute, but will still set the centroid to ``None`` to reflect the fact
    that we're not able to handle the entity's location.

    :param entity: the entity to modify.
    """
    location = LocationAttribute(entity)
    geojson_location = location.as_geojson()

    if geojson_location:
        entity[LOCATION_ATTR_NAME] = geojson_location

        centroid = location.compute_centroid()
        if centroid:
            entity[CENTROID_ATTR_NAME] = centroid.to_ngsi_attribute()

    elif entity:
        entity.pop(CENTROID_ATTR_NAME, None)
