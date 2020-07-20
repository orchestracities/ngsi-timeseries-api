from conftest import crate_translator as translator
from reporter.tests.test_1T1E1A import query_url as query_1T1E1A, \
    assert_1T1E1A_response
from reporter.tests.utils import get_notification, send_notifications
import requests
import time


def check_time_index(input_index, expected_index=None):
    expected_index = expected_index or input_index

    n0 = get_notification('Room', 'Room0', 0, input_index[0])
    n1 = get_notification('Room', 'Room0', 1, input_index[1])
    n2 = get_notification('Room', 'Room0', 2, input_index[2])

    send_notifications(service='', notifications=[n0, n1, n2])
    time.sleep(1)

    # Query
    r = requests.get(query_1T1E1A(), params={'type': 'Room'})
    assert r.status_code == 200, r.text
    obtained = r.json()

    # Check Response
    expected = {
        'entityId': 'Room0',
        'attrName': 'temperature',
        'index': expected_index,
        'values': [0, 1, 2]
    }
    assert_1T1E1A_response(obtained, expected)


def test_index_iso(translator):
    # If notifications use time-zone info, QL still responds in UTC
    input_index = [
        '2010-10-10T09:09:00.792',
        '2010-10-10T09:09:01.792',
        '2010-10-10T09:09:02.792',
    ]
    expected_index = [
        '2010-10-10T07:09:00.792+00:00',
        '2010-10-10T07:09:01.792+00:00',
        '2010-10-10T07:09:02.792+00:00',
    ]
    check_time_index(input_index, expected_index)


def test_index_iso_with_time_zone(translator):
    # If notifications use time-zone info, QL still responds in UTC
    # #97: Make it return time info used in input.
    input_index = [
        '2010-10-10T09:09:00.792+02:00',
        '2010-10-10T09:09:01.792+02:00',
        '2010-10-10T09:09:02.792+02:00',
    ]
    expected_index = [
        '2010-10-10T07:09:00.792+00:00',
        '2010-10-10T07:09:01.792+00:00',
        '2010-10-10T07:09:02.792+00:00',
    ]
    check_time_index(input_index, expected_index)
