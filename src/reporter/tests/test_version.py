from conftest import QL_BASE_URL
from _version import __dev_version__
import requests


def test_version():
    version_url = "{}/version".format(QL_BASE_URL)
    r = requests.get('{}'.format(version_url))
    assert r.status_code == 200, r.text
    assert r.json() == {
        "version": __dev_version__
    }
