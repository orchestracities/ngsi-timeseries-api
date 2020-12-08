from conftest import QL_BASE_URL
import pytest
import requests


def test_health_pass():
    """
    At the time test starts, services are already deployed.
    """
    url = '{}/health'.format(QL_BASE_URL)

    r = requests.get(url)
    assert r.status_code == 200, r.text
    assert r.headers['Cache-Control'] == 'max-age=180'

    response = r.json()
    assert response == {'status': 'pass'}


@pytest.mark.skip(reason="We need a new testing plan for this")
def test_health_warn_osm():
    """
    Run this test disabling access to Open Street Map (e.g. no internet).
    """
    url = '{}/health'.format(QL_BASE_URL)
    r = requests.get(url)

    assert r.status_code == 200, r.text
    response = r.json()
    assert response['status'] == 'warn'
    health = response['details']['osm']
    assert health['status'] == 'fail'
    assert 'time' in health
    assert 'ConnectionError' in health['output']


@pytest.mark.skip(reason="We need a new testing plan for this")
def test_health_fail_redis():
    """
    Run this test just without redis.

    e.g. docker-compose scale redis=0
    """
    url = '{}/health'.format(QL_BASE_URL)
    r = requests.get(url)

    assert r.status_code == 503, r.text
    response = r.json()
    assert response['status'] == 'fail'
    health = response['details']['redis']
    assert health['status'] == 'fail'
    assert 'time' in health
    assert 'Connection refused' in health['output']


@pytest.mark.skip(reason="We need a new testing plan for this")
def test_health_fail_crate():
    """
    Run this test with no crateDB.

    e.g. docker-compose scale crate=0
    """
    url = '{}/health'.format(QL_BASE_URL)
    r = requests.get(url)

    assert r.status_code == 503, r.text
    response = r.json()
    assert response['status'] == 'fail'
    health = response['details']['crateDB']
    assert health['status'] == 'fail'
    assert 'time' in health
    assert 'output' in health and health['output'] != ''
