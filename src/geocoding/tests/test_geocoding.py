"""
Tests of this module depends on external connectivity and availability of
openstreetmap services.
"""
from conftest import REDIS_HOST, REDIS_PORT
from geocoding import geocoding
import copy
import geojson
import pytest
from exceptions.exceptions import InvalidNGSIEntity


def assert_lon_lat(entity, expected_lon, expected_lat):
    assert 'location' in entity
    assert entity['location']['type'] == 'geo:point'

    lon, lat = entity['location']['value'].split(',')
    assert float(lon) == pytest.approx(expected_lon, abs=1e-2)
    assert float(lat) == pytest.approx(expected_lat, abs=1e-2)


def test_valid_address():
    geocoding.is_valid_address(None, 10, None, None, None)[0] is False
    geocoding.is_valid_address("Via San Gottardo", None, None, None, None)[
        0] is False
    geocoding.is_valid_address(None, None, None, None, None)[0] is False
    geocoding.is_valid_address(None, None, None, None, "Italy")[0] is True
    geocoding.is_valid_address(None, None, "Milan", None, None)[0] is True
    geocoding.is_valid_address("Via San Gottardo", None, "Milan", None, None)[
        0] is True


def test_non_dict_entity():
    entity = "string"

    try:
        geocoding.add_location(entity)
    except Exception as e:
        assert isinstance(e, TypeError)


def test_empty_dict_entity():
    entity = dict()
    try:
        geocoding.add_location(entity)
    except Exception as e:
        assert isinstance(e, InvalidNGSIEntity)


def test_no_address_entity():
    entity = {
        'id': 'test-id',
        'type': 'test-type'
    }
    res = geocoding.add_location(entity)
    assert 'address' not in res
    assert 'location' not in res


def test_entity_with_location(air_quality_observed):
    # Adding location to an entity with location does nothing
    assert 'location' in air_quality_observed
    old_entity = copy.copy(air_quality_observed)

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed
    assert r == old_entity


def test_entity_with_non_dict_address(air_quality_observed):
    air_quality_observed.pop('location')
    air_quality_observed['address']['value'] = "string address"

    old_entity = copy.copy(air_quality_observed)

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed
    assert r == old_entity


def test_entity_add_point(air_quality_observed):
    air_quality_observed.pop('location')

    air_quality_observed['address']['value'] = {
        "streetAddress": "IJzerlaan",
        "postOfficeBoxNumber": "18",
        "addressLocality": "Antwerpen",
        "addressCountry": "BE",
    }

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed

    assert_lon_lat(r, expected_lon=51.23, expected_lat=4.42)


def test_entity_add_point_negative_coord(air_quality_observed):
    air_quality_observed.pop('location')

    air_quality_observed['address']['value'] = {
        "streetAddress": "Calle Acolman",
        "postOfficeBoxNumber": "22",
        "postalCode": "55120",
        "addressLocality": "Ecatepec de Morelos",
        "addressCountry": "MX",
    }

    r = geocoding.add_location(air_quality_observed)
    assert r is air_quality_observed

    assert_lon_lat(r, expected_lon=19.5411019, expected_lat=-99.0341571)


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
    assert len(geo['coordinates']) > 1


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
    polygon = geojson.Polygon(geo['coordinates'])
    assert polygon.is_valid


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
    multi_polygon = geojson.MultiPolygon(geo['coordinates'])
    assert multi_polygon.is_valid


def test_multiple_entities(air_quality_observed):
    entity_2 = copy.copy(air_quality_observed)

    r = geocoding.add_locations([air_quality_observed, entity_2])
    assert isinstance(r, list)
    assert len(r) == 2


def test_caching(docker_redis, air_quality_observed, monkeypatch):
    air_quality_observed.pop('location')

    air_quality_observed['address']['value'] = {
        "streetAddress": "IJzerlaan",
        "postOfficeBoxNumber": "18",
        "addressLocality": "Antwerpen",
        "addressCountry": "BE",
    }

    from geocoding.geocache import temp_geo_cache
    cache = next(temp_geo_cache(REDIS_HOST, REDIS_PORT))
    assert len(cache.redis.keys('*')) == 0

    try:
        r = geocoding.add_location(air_quality_observed, cache=cache)
        assert r is air_quality_observed
        assert_lon_lat(r, expected_lon=51.23, expected_lat=4.42)
        assert len(cache.redis.keys('*')) == 1

        # Make sure no external calls are made
        monkeypatch.delattr("requests.sessions.Session.request")

        r.pop('location')
        r = geocoding.add_location(air_quality_observed, cache=cache)
        assert_lon_lat(r, expected_lon=51.23, expected_lat=4.42)
        assert len(cache.redis.keys('*')) == 1

    finally:
        cache.redis.flushall()


def test_health():
    geocoding.get_health()['status'] == 'pass'
