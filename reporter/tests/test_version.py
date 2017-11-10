from client.client import HEADERS
from conftest import QL_URL
import requests


def test_version():
    version_url = "{}/version".format(QL_URL)
    r = requests.get('{}'.format(version_url), headers=HEADERS)
    assert r.status_code == 200, r.text
    assert r.text == '{\n  "version": "0.1.0"\n}\n'
