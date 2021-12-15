# To test a single translator use the -k parameter followed by either
# timescale or crate.
# See https://docs.pytest.org/en/stable/example/parametrize.html

from exceptions.exceptions import AmbiguousNGSIIdError
from translators.base_translator import BaseTranslator
from translators.sql_translator import NGSI_TEXT, NGSI_DATETIME, NGSI_STRUCTURED_VALUE
from utils.common import *
from utils.tests.common import *
from datetime import datetime, timezone

from conftest import crate_translator, timescale_translator, entity
import pytest

from exceptions.exceptions import InvalidParameterValue

translators = [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
]

@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_ngsi_ld(translator, ngsi_ld):
    # Add TIME_INDEX as Reporter would
    now = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    ngsi_ld[TIME_INDEX_NAME] = now

    translator.insert([ngsi_ld])
    loaded, err = translator.query()

    assert ngsi_ld['id'] == loaded[0]['id']
    assert ngsi_ld['refStreetlightModel']['object'] == loaded[0]['refStreetlightModel']['values'][0]
    assert ngsi_ld['location']['value'] == loaded[0]['location']['values'][0]

    translator.clean()
