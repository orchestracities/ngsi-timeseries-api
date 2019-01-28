"""
Tests of this module depends on external connectivity and availability of
openstreetmap services.
"""
from conftest import REDIS_HOST, REDIS_PORT
from geocoding import geocoding
import copy
import pytest


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


@pytest.mark.skip(reason="See issue #105")
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

    assert 'location' in r
    assert r['location']['type'] == 'geo:point'

    lon, lat = r['location']['value'].split(',')
    assert float(lon) == pytest.approx(51.2358357, abs=1e-2)
    assert float(lat) == pytest.approx(4.4201911, abs=1e-2)


def test_entity_add_point_negative_coord(air_quality_observed):
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
    assert r['location']['type'] == 'geo:point'

    lon, lat = r['location']['value'].split(',')
    assert float(lon) == pytest.approx(19.6389474, abs=1e-2)
    assert float(lat) == pytest.approx(-98.9109537, abs=1e-2)


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


@pytest.mark.skip(reason="See issue #105")
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
    assert len(geo['coordinates'][0]) == pytest.approx(2186, abs=100)


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
    assert len(geo['coordinates']) == pytest.approx(12, abs=2)


def test_multiple_entities(air_quality_observed):
    entity_2 = copy.copy(air_quality_observed)

    r = geocoding.add_locations([air_quality_observed, entity_2])
    assert isinstance(r, list)
    assert len(r) == 2


@pytest.mark.skip(reason="See issue #105")
def test_caching(air_quality_observed, monkeypatch):
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
        assert 'location' in r
        assert r['location']['type'] == 'geo:point'
        lon, lat = r['location']['value'].split(',')
        assert float(lon) == pytest.approx(51.2358357, abs=1e-2)
        assert float(lat) == pytest.approx(4.4201911, abs=1e-2)
        assert len(cache.redis.keys('*')) == 1

        # Make sure no external calls are made
        monkeypatch.delattr("requests.sessions.Session.request")

        r.pop('location')
        r = geocoding.add_location(air_quality_observed, cache=cache)
        assert 'location' in r
        assert r['location']['type'] == 'geo:point'
        lon, lat = r['location']['value'].split(',')
        assert float(lon) == pytest.approx(51.2358357, abs=1e-2)
        assert float(lat) == pytest.approx(4.4201911, abs=1e-2)
        assert len(cache.redis.keys('*')) == 1

    finally:
        cache.redis.flushall()
