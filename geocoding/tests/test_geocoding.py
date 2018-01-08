"""
Tests of this module depends on external connectivity and availability of
openstreetmap services.
"""
from conftest import air_quality_observed, REDIS_HOST, REDIS_PORT
from geocoding import geocoding
import copy
import json


def test_entity_with_location(air_quality_observed):
    # Adding location to an entity with location does nothing
    assert 'location' in air_quality_observed
    old_entity = copy.copy(air_quality_observed)

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed
    assert r == old_entity


def test_entity_add_point(air_quality_observed):
    air_quality_observed.pop('location')

    air_quality_observed['address']['value'] = {
        "streetAddress": "Acolman",
        "postOfficeBoxNumber": "22",
        "addressLocality": "Ciudad de México",
        "addressCountry": "MX",
    }

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed

    assert 'location' in r
    assert r['location']['type'] == 'geo:json'

    geo = r['location']['value']['geometry']
    assert geo['type'] == 'Point'
    assert len(geo['coordinates']) == 2


def test_entity_add_street_line(air_quality_observed):
    air_quality_observed.pop('location')

    air_quality_observed['address']['value'] = {
        "streetAddress": "Acolman",
        "addressLocality": "Ciudad de México",
        "addressCountry": "MX",
    }

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed

    assert 'location' in r
    assert r['location']['type'] == 'geo:json'

    geo = r['location']['value']
    assert geo['type'] == 'LineString'
    assert len(geo['coordinates']) == 12


def test_entity_add_city_shape(air_quality_observed):
    air_quality_observed.pop('location')

    air_quality_observed['address']['value'] = {
        "addressCountry": "MX",
        "addressLocality": "Ciudad de México",
    }

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed

    assert 'location' in r
    assert r['location']['type'] == 'geo:json'

    geo = r['location']['value']
    assert geo['type'] == 'Polygon'
    assert len(geo['coordinates']) == 1
    assert len(geo['coordinates'][0]) == 2186


def test_entity_add_country_shape(air_quality_observed):
    air_quality_observed.pop('location')

    air_quality_observed['address']['value'] = {
        "addressCountry": "MX",
    }

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed

    assert 'location' in r
    assert r['location']['type'] == 'geo:json'

    geo = r['location']['value']
    assert geo['type'] == 'MultiPolygon'
    assert len(geo['coordinates']) == 12


def test_multiple_entities(air_quality_observed):
    entity_2 = copy.copy(air_quality_observed)

    r = geocoding.add_locations([air_quality_observed, entity_2])
    assert isinstance(r, list)
    assert len(r) == 2


def test_caching(air_quality_observed):
    air_quality_observed.pop('location')

    air_quality_observed['address']['value'] = {
        "streetAddress": "Acolman",
        "postOfficeBoxNumber": "22",
        "addressLocality": "Ciudad de México",
        "addressCountry": "MX",
    }

    from geocoding.geocache import GeoCodingCache
    cache = GeoCodingCache(REDIS_HOST, REDIS_PORT)
    value = {'type': 'Point', 'coordinates': [-98.9109537, 19.6389474]}
    cache.put('Acolman 22 , Ciudad de México , MX', json.dumps(value))

    r = geocoding.add_location(air_quality_observed, cache=cache)
    assert r is air_quality_observed

    assert 'location' in r
    assert r['location']['type'] == 'geo:json'
    assert r['location']['value'] == value
