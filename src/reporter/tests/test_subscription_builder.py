import pytest

from reporter.subscription_builder import build_subscription


def test_bare_subscription():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                    'idPattern': '.*'
                }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified']
        },
        'throttling': 1
    }

    assert actual == expected


def test_entity_type():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype='gauge', eid=None, eid_pattern=None,
        observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'type': 'gauge',
                'idPattern': '.*'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified']
        },
        'throttling': 1
    }

    assert actual == expected


def test_entity_id():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=123, eid_pattern=None,
        observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'id': '123'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.parametrize('attrs', ['a1', 'a1,a2', 'a1,a2,a3'])
def test_observed_attributes(attrs):
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        observed_attributes=attrs, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }],
            'condition': {
                'attrs': attrs.split(',')
            }
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified']
        },
        'throttling': 1
    }

    assert actual == expected


@pytest.mark.parametrize('attrs', ['a1', 'a1,a2', 'a1,a2,a3'])
def test_notified_attributes(attrs):
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        observed_attributes=None, notified_attributes=attrs,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'attrs': attrs.split(','),
            'metadata': ['dateCreated', 'dateModified']
        },
        'throttling': 1
    }

    assert actual == expected


def test_throttling():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        observed_attributes=None, notified_attributes=None,
        throttling_secs=123)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified']
        },
        'throttling': 123
    }

    assert actual == expected


def test_entity_id_overrides_pattern():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid='e123', eid_pattern='e1.*',
        observed_attributes=None, notified_attributes=None,
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'id': 'e123'
            }]
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'metadata': ['dateCreated', 'dateModified']
        },
        'throttling': 1
    }

    assert actual == expected


def test_all_attributes():
    actual = build_subscription(
        quantumleap_url='http://ql',
        etype=None, eid=None, eid_pattern=None,
        observed_attributes='a,b', notified_attributes='b,c',
        throttling_secs=None)
    expected = {
        'description': 'Created by QuantumLeap http://ql.',
        'subject': {
            'entities': [{
                'idPattern': '.*'
            }],
            'condition': {
                'attrs': ['a', 'b']
            }
        },
        'notification': {
            'http': {
                'url': 'http://ql/notify'
            },
            'attrs': ['b', 'c'],
            'metadata': ['dateCreated', 'dateModified']
        },
        'throttling': 1
    }

    assert actual == expected
