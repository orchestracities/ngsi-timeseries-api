import default


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200, r.text
    assert r.json() == {
        "v2": "/v2"
    }


def test_version(client):
    r = client.get("/version")
    assert r.status_code == 200, r.text
    assert r.json() == {
        "version": default.VERSION
    }


def test_v2(client):
    r = client.get("/v2")
    assert r.status_code == 200, r.text
    assert r.json() == {
        "notify_url": "/v2/notify",
        "subscriptions_url": "/v2/subscriptions",
        "entities_url": "/v2/entities",
        "types_url": "/v2/types",
        "attributes_url": "/v2/attrs"
    }
