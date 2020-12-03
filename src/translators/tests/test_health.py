# To test a single translator use the -k parameter followed by either
# timescale or crate.
# See https://docs.pytest.org/en/stable/example/parametrize.html

from conftest import crate_translator, timescale_translator

import pytest

translators = [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
]


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_health(translator):
    health = translator.get_health()
    assert health['status'] == 'pass'
