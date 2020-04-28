import requests
from src.tests.common import QL_URL
from typing import Optional

ALLOWED_ORIGIN_HEADER: str = "Access-Control-Allow-Origin";
ORIGIN_HEADER: str = "Origin";


def test_cors_set_allowed_headers():
    origin: str = "http://localhost"
    res: requests.Response = requests.options("{}/v2/".format(QL_URL),
                                              headers={ORIGIN_HEADER: origin})
    assert res.ok, "OPTIONS request failed: " + str(res.status_code)
    origin_header: Optional[str] = res.headers.get(ALLOWED_ORIGIN_HEADER)
    assert origin_header == origin, "Unexpected origin header: " + str(origin_header)


def test_cors_notset_allowed_headers():
    res: requests.Response = requests.options("{}/v2/".format(QL_URL),
                                              headers={ORIGIN_HEADER: "http://localhost"})
    assert res.ok, "OPTIONS request failed: " + str(res.status_code)
    origin_header: Optional[str] = res.headers.get(ALLOWED_ORIGIN_HEADER)
    assert origin_header is None, "Unexpected origin header: " + str(origin_header)