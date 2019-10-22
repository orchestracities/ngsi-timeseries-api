from conftest import QL_URL, crate_translator as translator
from exceptions.exceptions import AmbiguousNGSIIdError
from reporter.tests.utils import insert_test_data
import pytest
import requests

entity_type = 'Room'
entity_id = 'Room0'

def query_url():
    url = "{qlUrl}/entities"

    return url.format(
        qlUrl=QL_URL
    )

@pytest.fixture()
def reporter_dataset(translator):
    insert_test_data(translator, [entity_type], n_entities=1, index_size=30)
    yield

def test_NTNE_defaults(reporter_dataset):

    r = requests.get(query_url())
    assert r.status_code == 200, r.text

    obtained = r.json()
    exp_values = ['Room0']

    expected = {
        'entityId': exp_values
    }
    assert obtained == expected

def test_not_found():
    r = requests.get(query_url())
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }
