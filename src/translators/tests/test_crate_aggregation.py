from conftest import crate_translator as translator
from utils.common import create_random_entities, TIME_INDEX_NAME, add_attr
import datetime


def test_aggr_per_second(translator):
    entities = create_random_entities(num_ids_per_type=2, num_updates=17)
    assert len(entities) == 34

    # One update every 100 millis -> 10 updates per second.
    base_index = datetime.datetime(2010, 1, 1, 8, 0, 0, 0, datetime.timezone.utc)
    delta = datetime.timedelta(milliseconds=100)
    for i, e in enumerate(entities):
        t = base_index + i * delta
        e[TIME_INDEX_NAME] = t.isoformat(timespec='milliseconds')
        add_attr(e, 'attr_float', i)

    translator.insert(entities)

    # Query avg attr_float per second.
    res = translator.query(attr_names=['attr_float'],
                           aggr_method='avg',
                           aggr_period='second')
    assert len(res) == 2

    # 34 values span across 4 seconds
    expected_index = []
    for i in range(4):
        d = datetime.datetime(2010, 1, 1, 8, 0, i, 0, datetime.timezone.utc)
        expected_index.append(d.isoformat(timespec='milliseconds'))

    assert res[0] == {
        'type': '0',
        'id': '0-0',
        'index': expected_index,
        'attr_float': {
            'type': 'Number',
            'values': [4, 14, 24, 31],
        }
    }
    assert res[1] == {
        'type': '0',
        'id': '0-1',
        'index': expected_index,
        'attr_float': {
            'type': 'Number',
            'values': [5, 15, 25, 32],
        }
    }
