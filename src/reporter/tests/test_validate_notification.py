import pytest
from reporter.reporter import is_text, has_value, _validate_payload


@pytest.mark.parametrize('attr_type, expected', [
    (None, True), ('', True), ('string', True), ('text', True), ('Text', True),
    ('Number', False), ('geo:json', False)
])
def test_is_text(attr_type, expected):
    assert is_text(attr_type) == expected


@pytest.mark.parametrize('entity', [
    {}, {'a': None}, {'a': {}}, {'a': {'type': None}},
    {'a': {'type': 'Text'}}, {'a': {'type': 'Text', 'value': None}},
    {'a': {'type': 'Number'}}, {'a': {'type': 'Number', 'value': None}},
    {'a': {'type': 'Number', 'value': ''}}
])
def test_has_no_value(entity):
    assert has_value(entity, None) is False
    assert has_value(entity, 'a') is False
    assert has_value(entity, 'b') is False


@pytest.mark.parametrize('entity', [
    {'a': {'type': 'Text', 'value': ''}},
    {'a': {'type': 'Text', 'value': 'x'}},
    {'a': {'type': 'Number', 'value': 0}}
])
def test_has_value(entity):
    assert has_value(entity, None) is False
    assert has_value(entity, 'a') is True
    assert has_value(entity, 'b') is False


def test_invalid_no_id():
    data = {
        'type': 'Room',
        'temperature': {
            'type': 'Number',
            'value': 50,
            'metadata': {
                'dateModified': {
                    'type': 'DateTime',
                    'value': '2018-01-01T11:46:45.000Z'
                }
            }
        }
    }
    assert _validate_payload(data) is not None


def test_invalid_no_type():
    data = {
        'id': 'Room:001',
        'temperature': {
            'type': 'Number',
            'value': 50,
            'metadata': {
                'dateModified': {
                    'type': 'DateTime',
                    'value': '2018-01-01T11:46:45.000Z'
                }
            }
        }
    }
    assert _validate_payload(data) is not None


def test_valid_no_attr():
    data = {
        'id': 'Room:001',
        'type': 'Room',
    }
    assert _validate_payload(data) is None


def test_valid_no_attr_type():
    data = {
        'id': 'Room:001',
        'type': 'Room',
        'temperature': {
            'value': 50,
            'metadata': {
                'dateModified': {
                    'type': 'DateTime',
                    'value': '2018-01-01T11:46:45.000Z'
                }
            }
        }
    }
    assert _validate_payload(data) is None
    assert data['temperature']['value'] == 50


def test_valid_no_attr_numeric_value():
    data = {
        'id': 'Room:001',
        'type': 'Room',
        'temperature': {
            'type': 'Number',
            'metadata': {
                'dateModified': {
                    'type': 'DateTime',
                    'value': '2018-01-01T11:46:45.000Z'
                }
            }
        }
    }
    assert _validate_payload(data) is None
    assert 'value' in data['temperature']
    assert data['temperature']['value'] is None


def test_valid_no_attr_text_value():
    data = {
        'id': 'Room:001',
        'type': 'Room',
        'temperature': {
            'type': 'Text',
            'metadata': {
                'dateModified': {
                    'type': 'DateTime',
                    'value': '2018-01-01T11:46:45.000Z'
                }
            }
        }
    }
    assert _validate_payload(data) is None
    assert 'value' in data['temperature']
    assert data['temperature']['value'] is None


def test_valid_empty_numeric_attr_value():
    # See also GH Issue #145
    data = {
        'id': 'Room:001',
        'type': 'Room',
        'temperature': {
            'type': 'Number',
            'value': '',
            'metadata': {
                'dateModified': {
                    'type': 'DateTime',
                    'value': '2018-01-01T11:46:45.000Z'
                }
            }
        },
        'proximity': {
            'type': 'Number',
            'value': ' ',
            'metadata': {}
        },
        'TimeStep': {
            'type': 'DateTime',
            'value': '',
            'metadata': {}
        },
        'TimeInstant': {
            'type': 'DateTime',
            'value': ' ',
            'metadata': {}
        },
    }

    assert _validate_payload(data) is None
    assert data['temperature']['value'] is None
    assert data['proximity']['value'] is None
    assert data['TimeStep']['value'] is None
    assert data['TimeInstant']['value'] is None


def test_valid_empty_textual_attr_value():
    data = {
        'id': 'Room:001',
        'type': 'Room',
        'temperature': {
            'type': 'Text',
            'value': '',
            'metadata': {
                'dateModified': {
                    'type': 'DateTime',
                    'value': '2018-01-01T11:46:45.000Z'
                }
            }
        }
    }
    assert _validate_payload(data) is None
    assert 'value' in data['temperature']
    assert data['temperature']['value'] is ''
