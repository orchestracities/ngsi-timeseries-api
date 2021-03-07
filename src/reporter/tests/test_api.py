from conftest import QL_URL
import requests


def test_api():
    api_url = "{}/".format(QL_URL)
    r = requests.get('{}'.format(api_url))
    assert r.status_code == 200, r.text
    assert r.json() == {
        "notify_url": "/v2/notify",
        "subscriptions_url": "/v2/subscriptions",
        "entities_url": "/v2/entities",
        "types_url": "/v2/types",
        "attributes_url": "/v2/attrs"
    }
