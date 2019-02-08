from datetime import *
from reporter.timex import *


def build_notification(custom, ti, dm, mti, mdm, a1_ti, a1_dm, a2_ti, a2_dm):
    return {
        'customTimeIndex': {
            'value': custom
        },
        'TimeInstant': {
            'value': ti
        },
        'dateModified': {
            'value': dm
        },
        'metadata': {
            'TimeInstant': {
                'value': mti
            },
            'dateModified': {
                'value': mdm
            }
        },
        'a1': {
            'metadata': {
                'TimeInstant': {
                    'value': a1_ti
                },
                'dateModified': {
                    'value': a1_dm
                }
            }
        },
        'a2': {
            'metadata': {
                'TimeInstant': {
                    'value': a2_ti
                },
                'dateModified': {
                    'value': a2_dm
                }
            }
        }
    }


def build_notification_timepoints(base_point):
    ts = []
    for k in range(9):
        d = base_point + timedelta(days=k)
        ts.append(d.isoformat())
    return ts


def test_custom_index_takes_priority():
    headers = {
        TIME_INDEX_HEADER_NAME: 'customTimeIndex'
    }
    custom_time_index_value = datetime(2019, 1, 1)
    ts = build_notification_timepoints(custom_time_index_value)
    notification = build_notification(*ts)

    assert custom_time_index_value == \
        select_time_index_value(headers, notification)


def test_skip_custom_index_if_it_has_no_value():
    headers = {
        TIME_INDEX_HEADER_NAME: 'customTimeIndex'
    }
    base_point = datetime(2019, 1, 1)
    ts = build_notification_timepoints(base_point)
    ts[0] = None  # custom index slot
    notification = build_notification(*ts)

    assert ts[1] == \
        select_time_index_value(headers, notification).isoformat()


def test_use_time_instant():
    headers = {}
    base_point = datetime(2019, 1, 1)
    ts = build_notification_timepoints(base_point)
    notification = build_notification(*ts)

    assert ts[1] == \
        select_time_index_value(headers, notification).isoformat()


def test_use_latest_meta_time_instant():
    headers = {}
    base_point = datetime(2019, 1, 1)

    ts = build_notification_timepoints(base_point)
    ts[1] = None  # time instant slot

    notification = build_notification(*ts)

    # latest meta time instant slot = 7
    assert ts[7] == \
        select_time_index_value(headers, notification).isoformat()


def test_use_latest_meta_date_modified():
    headers = {}
    base_point = datetime(2019, 1, 1)

    ts = build_notification_timepoints(base_point)
    ts[1] = None  # time instant slot
    ts[2] = None  # date modified
    ts[3] = None  # meta time instant
    ts[5] = None  # a1 time instant
    ts[7] = None  # a2 time instant

    notification = build_notification(*ts)

    # latest meta date modified slot = 8
    assert ts[8] == \
        select_time_index_value(headers, notification).isoformat()


def test_use_date_modified():
    headers = {}
    base_point = datetime(2019, 1, 1)

    ts = build_notification_timepoints(base_point)
    ts[1] = None  # time instant slot
    ts[3] = None  # meta time instant
    ts[5] = None  # a1 time instant
    ts[7] = None  # a2 time instant

    notification = build_notification(*ts)

    # date modified slot = 2
    assert ts[2] == \
        select_time_index_value(headers, notification).isoformat()


def test_use_default_value():
    headers = {}
    notification = build_notification(None, None, None, None, None, None, None,
                                      None, None)

    actual = select_time_index_value(headers, notification)
    diff = datetime.now() - actual
    assert diff < timedelta(seconds=2)
