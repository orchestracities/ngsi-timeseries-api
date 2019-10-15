from conftest import QL_URL
import requests


def test_version():
    version_url = "{}/version".format(QL_URL)
    QL_version_url = version_url.replace("/v2","")
    r = requests.get('{}'.format(QL_version_url))
    assert r.status_code == 200, r.text
    assert r.json() == {
        "version": "0.7.5"
    }
def test_version_v2():
    version_url = "{}/version".format(QL_URL)
    r = requests.get('{}'.format(version_url))
    assert r.status_code == 404, r.text
    assert r.json() == {
    "detail": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
    "status": 404,
    "title": "Not Found",
    "type": "about:blank"
    }
