"""
This module is designed to complement QuantumLeap in the treatment of NGSI
entities containing geo-data attributes.

The main usage: call method 'add_location' passing your entity. If the entity
has an attribute called 'address' and does not have an attribute called
'location', this function will add a 'location' attribute with a geo-json
attribute generated out of the information found in the 'address' attribute.

The 'address' attribute should be a dict like the one called 'address' in
Common-Locations as can be seen here:
https://github.com/Fiware/dataModels/blob/master/common-schema.json

This service requires external connectivity in order to fetch data from
'openstreetmaps.org' and its 'nominatim' service. This is to do the geocoding
from the address data to a geo:json structure.

The returned structure can be a Point, a LineString (for streets) or a
MultiPolygon (for states or countries). In the case of a point, a geo:point
attribute will be created. Otherwise, geo:json will be preferred.

If you provide all the fields of the 'address' dict, it is assumed you are
looking for a Point. If you omit the 'postOfficeBoxNumber' but include the
'streetAddress', it is assumed you are looking for a street (LineString). If
you omit both number and street number, the response will be a shape of
either the city or country you specified in the 'addressLocality' or
'addressCountry' fields respectively. Remember 'addressCountry' is expected to
be an ISO Alpha-2 Country Code.

# TODO: Parametrize OpenStreetMap server address so that we can encourage the
usage of custom offline Nominatim servers.

IDEAS for future improvements:
- We could support in address a custom field that bypasses all the rest,
which will be the search term for osm. This is to cover cases where you want
a point but don't necessary have a street + postOfficeBoxNumber. For example,
"Eiffel Tower, Paris".
"""
import asyncio
from datetime import datetime
from geopy.adapters import AioHTTPAdapter
from geopy.geocoders import Nominatim
import json
import logging

from exceptions.exceptions import InvalidNGSIEntity

logger = logging.getLogger(__name__)

TYPE_POINT = 0
TYPE_WAY = 1
TYPE_RELATION = 2


def add_locations(entities, raise_error=False):
    result = []
    for e in entities:
        result.append(
            add_location(e, raise_error=raise_error)
        )
    return result


def add_location(entity, raise_error=False, cache=None):
    """
    :param dict entity:
        A valid NGSI entity, as usual, expected in JSON Entity Representation.

    :return:
        The same entity, but if the entity did not have a 'location' attribute,
        this method will add it. In this case, entity is expected to have an
        'address' attribute, like the one found in Location-Commons in
        https://github.com/Fiware/dataModels/blob/master/common-schema.json.

        Location will be a geojson, determined by the geoquery using the
        address information. The address information needs at least two
        attributes, one of which must be either the City

        If the address has

        Values of the point are [longitude, latitude].

        If the method cannot determine a location, it simply returns the entity
        as it was, unless you set raise_error, in which case a RuntimeError
        is raised.
    """
    # Validate Entity
    if not isinstance(entity, dict):
        raise TypeError

    if 'type' not in entity or 'id' not in entity:
        raise InvalidNGSIEntity(entity)

    if 'location' in entity:
        return entity

    if 'address' not in entity:
        error_msg = 'Cannot add location to entity ' \
                    '(type: "{}", id: "{}")'.format(entity['type'],
                                                    entity['id'])
        logger.warning('{}, missing "address" attribute.'.format(error_msg))
        return entity

    addr = entity['address']
    if not isinstance(addr, dict) or not isinstance(addr['value'], dict):
        error_msg = 'Attribute address in entity (type: "{}", id: "{}")' \
                    'is not a dict, so geocoding will not act.'
        logger.warning(error_msg.format(entity['type'], entity['id']))
        return entity

    # Get Address Key
    key, osm_type = get_address_key_and_type(entity)

    # Get Location from Cache (if any)
    if cache:
        loc = cache.get(key)
        if loc is not None:
            return _do_add_location(entity, json.loads(loc))

    # Get Location from Provider (if possible)
    info = None
    try:
        info = asyncio.run(geocode(key))

    except Exception as e:
        logging.error(repr(e))
        if raise_error:
            raise e
        return entity

    if not info:
        msg = "Request to provider was not OK. {}".format(info)
        logging.error(msg)
        if raise_error:
            raise RuntimeError(msg)
        return entity

    # Extract location from result.
    loc = None
    if osm_type == TYPE_POINT:
        loc = _extract_point(info)

    elif osm_type == TYPE_WAY:
        # We are looking for a street
        for i in info:
            if i.raw['osm_type'] == 'way':
                loc = i.raw['geojson']
                break

    elif osm_type == TYPE_RELATION:
        # We are looking for a state or country
        for i in info:
            if i.raw['osm_type'] == 'relation':
                loc = i.raw['geojson']
                break

    if loc is None:
        msg = "Could not determine location of type {} for key {}."
        logging.error(msg.format(osm_type, key))
        return entity

    if cache:
        cache.put(key, json.dumps(loc))

    return _do_add_location(entity, loc)


def _osm_result_geom_type(result):
    if 'geojson' in result.raw and isinstance(result.raw['geojson'], dict):
        return result.raw['geojson'].get('type', '')
    return None


def _extract_most_accurate_osm_result(osm_response, geom_type):
    results = sorted(osm_response, key=lambda r: r.raw['importance'])
    results_of_specified_type = [r for r in results
                                 if geom_type == _osm_result_geom_type(r)]
    if len(results_of_specified_type) > 0:
        return results_of_specified_type[0].geojson
    elif geom_type == 'Point' and len(results) > 0:
        return {
            'type': 'geo:point',
            'value': "{}, {}".format(
                results[0].latitude,
                results[0].longitude)}
    return None


def _extract_point(osm_response):
    return _extract_most_accurate_osm_result(osm_response, 'Point')


def _do_add_location(entity, location):
    # Inject location into entity respecting its representation format
    assert isinstance(location, dict)
    is_json_repr = 'value' in entity['address']

    if is_json_repr:
        if location.get('type') == 'geo:point':
            entity['location'] = location
        else:
            entity['location'] = {
                'type': 'geo:json',
                'value': location
            }
    else:
        entity['location'] = location

    return entity


def get_address_key_and_type(entity):
    """
    :return: unicode
        The address to be used as a key in the geocoding call. The address
        is composed of a comma-separated list of the relevant address elements.
        E.g: 'Gran via 9, Madrid, ES'

        NOTE: Alternatively we could avoid this key composition and align
        better with the supported query attributes. See
        https://wiki.openstreetmap.org/wiki/Nominatim#Examples
    """
    is_json_repr = 'value' in entity['address']
    if is_json_repr:
        # JSON Attribute Representation, as expected by QL in /notify
        address = entity['address']['value']
    else:
        # Simplified Entity Representation support
        address = entity['address']

    street = address.get('streetAddress', '')
    number = address.get('postOfficeBoxNumber', '')

    postal_code = address.get('postalCode', '')
    locality = address.get('addressLocality', '')
    region = address.get('addressRegion', '')
    country = address.get('addressCountry', '')

    valid, msg = is_valid_address(street, number, locality, region, country)
    if not valid:
        raise ValueError(msg)

    if street:
        osm_type = TYPE_WAY if not number else TYPE_POINT
    else:
        osm_type = TYPE_RELATION

    key = ""
    if street:
        key += "{} ".format(street)
    if number:
        key += "{} ".format(number)
    if street or number:
        key += ', '

    if locality:
        key += "{} ".format(locality)
    if postal_code:
        key += "{} ".format(postal_code)
    if region:
        key += "{} ".format(region)
    if (locality or postal_code or region) and country:
        key += ', '

    if country:
        key += "{}".format(country)

    return key, osm_type


def is_valid_address(street, number, locality, region, country):
    if number and not street:
        return False, "Street name (streetAddress) is required when providing" \
                      " street number (postOfficeBoxNumber)."

    if not (street or locality or country):
        return False, "Missing address information, please specify either of " \
                      "the following: 'streetAddress', 'addressLocality', " \
                      "'addressCountry'."

    if street and not (locality or region or country):
        return False, "Street name (streetAddress) must be accompanied of " \
                      "'addressLocality', 'addressRegion' or 'addressCountry'."

    return True, "OK"


async def geocode(key: str):
    async with Nominatim(
            user_agent="quantumleap",
            adapter_factory=AioHTTPAdapter,
    ) as geolocator:
        info = await geolocator.geocode(key, geometry='geojson', exactly_one=False, limit=5, timeout=30)
        return info


def get_health():
    """
    :return: dictionary with geocoder service health. ::see:: reporter.health.
    """
    try:
        location = asyncio.run(geocode("New York City"))
    except (Exception) as e:
        # geocoder docs say exception will be raised to the caller
        time = datetime.now().isoformat()
        output = "{}".format(e)
        res = {'status': 'fail', 'time': time, 'output': output}
        return res
    else:
        if location:
            return {'status': 'pass'}

        time = datetime.now().isoformat()
        res = {'status': 'fail', 'time': time, 'output': location}
        return res
