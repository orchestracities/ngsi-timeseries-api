import pytest
from dateutil.tz import tzutc
from utils.timestr import *


# see: https://stackoverflow.com/questions/127803
@pytest.mark.parametrize('string_rep, expected', [
    (None, None), ('', None), (' ', None), ('\t', None), ('\n', None),
    ('2008-09-03T20:56:35.450686Z',     # RFC 3339 format
        datetime(2008, 9, 3, 20, 56, 35, 450686, tzinfo=tzutc())),
    ('2008-09-03T20:56:35.450686',      # ISO 8601 extended format
        datetime(2008, 9, 3, 20, 56, 35, 450686)),
    ('20080903T205635.450686',          # ISO 8601 basic format
        datetime(2008, 9, 3, 20, 56, 35, 450686)),
    ('20080903',                        # ISO 8601 basic format, date only
        datetime(2008, 9, 3, 0, 0))
])
def test_to_datetime(string_rep, expected):
    assert expected == to_datetime(string_rep)


@pytest.mark.parametrize('timepoints, expected', [
    ([], None),
    ([datetime(2019, 2, 1)], datetime(2019, 2, 1)),
    ([datetime(2019, 2, 1), datetime(2018, 1, 1)], datetime(2019, 2, 1)),
    ([datetime(2019, 1, 1), datetime(2019, 2, 1), datetime(2018, 1, 1)],
     datetime(2019, 2, 1))
])
def test_latest(timepoints, expected):
    assert expected == latest(timepoints)


@pytest.mark.parametrize('str_reps, expected', [
    ([], None), (['', None, ' '], None),
    (['20190201', ''], datetime(2019, 2, 1)),
    (['20190201', None, '20180101', 'xxx'], datetime(2019, 2, 1)),
    (['20190101', '20190201', '20180101', None, ''],
     datetime(2019, 2, 1))
])
def test_latest_from_str_rep(str_reps, expected):
    assert expected == latest_from_str_rep(str_reps)
