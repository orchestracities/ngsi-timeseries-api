from conftest import QL_BASE_URL
import requests


def test_version():
    version_url = "{}/version".format(QL_BASE_URL)
    r = requests.get('{}'.format(version_url))
    assert r.status_code == 200, r.text
    assert r.json() == {
        "version": "0.9.0-dev"
    }
