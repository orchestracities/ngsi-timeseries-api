from datetime import *
from reporter.timex import *
import pytest


def build_notification(custom, ti, ts, dm,
                       a1_custom, a1_ti, a1_ts, a1_dm,
                       a2_custom, a2_ti, a2_ts, a2_dm):
    return {
        'customTimeIndex': {
            'value': custom
        },
        'TimeInstant': {
            'value': ti
        },
        'timestamp': {
            'value': ts
        },
        'dateModified': {
            'value': dm
        },
        'a1': {
            'metadata': {
                'customTimeIndex': {
                    'value': a1_custom
                },
                'TimeInstant': {
                    'value': a1_ti
                },
                'timestamp': {
                    'value': a1_ts
                },
                'dateModified': {
                    'value': a1_dm
                }
            }
        },
        'a2': {
            'metadata': {
                'customTimeIndex': {
                    'value': a2_custom
                },
                'TimeInstant': {
                    'value': a2_ti
                },
                'timestamp': {
                    'value': a2_ts
                },
                'dateModified': {
                    'value': a2_dm
                }
            }
        }
    }


def build_notification_timepoints(base_point):
    ts = []
    for k in range(12):
        d = base_point + timedelta(days=k)
        ts.append(d.isoformat())
    return ts


def test_custom_index_takes_priority():
    custom_time_index_value = datetime(2019, 1, 1)
    ts = build_notification_timepoints(custom_time_index_value)
    notification = build_notification(*ts)

    assert custom_time_index_value == \
        select_time_index_value('customTimeIndex', notification)


def test_use_latest_meta_custom_index():
    base_point = datetime(2019, 1, 1)

    ts = build_notification_timepoints(base_point)
    ts[0] = None  # custom index attribute slot

    notification = build_notification(*ts)

    # latest meta custom index slot = 8
    assert ts[8] == \
        select_time_index_value('customTimeIndex', notification).isoformat()


def test_skip_custom_index_if_it_has_no_value():
    base_point = datetime(2019, 1, 1)
    ts = build_notification_timepoints(base_point)
    ts[0] = None  # custom index slot
    ts[4] = None  # custom index metadata for a1
    ts[8] = None  # custom index metadata for a2
    notification = build_notification(*ts)

    assert ts[1] == \
        select_time_index_value('customTimeIndex', notification).isoformat()


def test_use_time_instant():
    base_point = datetime(2019, 1, 1)
    ts = build_notification_timepoints(base_point)
    notification = build_notification(*ts)

    assert ts[1] == \
        select_time_index_value(None, notification).isoformat()


def test_use_latest_meta_time_instant():
    base_point = datetime(2019, 1, 1)

    ts = build_notification_timepoints(base_point)
    ts[1] = None  # time instant slot

    notification = build_notification(*ts)

    # latest meta time instant slot = 9
    assert ts[9] == \
        select_time_index_value(None, notification).isoformat()


def test_use_timestamp():
    base_point = datetime(2019, 1, 1)
    ts = build_notification_timepoints(base_point)
    ts[1] = None  # TimeInstant slot
    ts[5] = None  # TimeInstant metadata for a1
    ts[9] = None  # TimeInstant metadata for a2
    notification = build_notification(*ts)

    assert ts[2] == \
        select_time_index_value(None, notification).isoformat()


def test_use_latest_meta_timestamp():
    base_point = datetime(2019, 1, 1)

    ts = build_notification_timepoints(base_point)
    ts[1] = None  # TimeInstant slot
    ts[2] = None  # timestamp slot
    ts[5] = None  # TimeInstant metadata for a1
    ts[9] = None  # TimeInstant metadata for a2

    notification = build_notification(*ts)

    # latest meta time instant slot = 10
    assert ts[10] == \
        select_time_index_value(None, notification).isoformat()


def test_use_date_modified():
    base_point = datetime(2019, 1, 1)

    ts = build_notification_timepoints(base_point)
    ts[1] = None  # time instant slot
    ts[2] = None  # timestamp slot
    ts[5] = None  # a1 time instant
    ts[6] = None  # a1 timestamp
    ts[9] = None  # a2 time instant
    ts[10] = None  # a2 timestamp

    notification = build_notification(*ts)

    # date modified slot = 3
    assert ts[3] == \
        select_time_index_value(None, notification).isoformat()


def test_use_latest_meta_date_modified():
    base_point = datetime(2019, 1, 1)

    ts = build_notification_timepoints(base_point)
    ts[1] = None  # time instant slot
    ts[2] = None  # timestamp slot
    ts[3] = None  # date modified slot
    ts[5] = None  # a1 time instant
    ts[6] = None  # a1 timestamp
    ts[9] = None  # a2 time instant
    ts[10] = None  # a2 timestamp

    notification = build_notification(*ts)

    # latest meta date modified slot = 11
    assert ts[11] == \
        select_time_index_value(None, notification).isoformat()


def test_use_default_value():
    notification = build_notification(*([None] * 12))

    actual = select_time_index_value(None, notification)
    diff = datetime.now() - actual
    assert diff < timedelta(seconds=2)
