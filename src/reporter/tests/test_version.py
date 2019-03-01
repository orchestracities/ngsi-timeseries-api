from conftest import QL_URL
import requests


def test_version():
    version_url = "{}/version".format(QL_URL)
    r = requests.get('{}'.format(version_url))
    assert r.status_code == 200, r.text
    assert r.json() == {
        "version": "0.6"
    }
