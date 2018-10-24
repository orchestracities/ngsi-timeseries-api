from conftest import crate_translator as translator
from utils.common import create_random_entities, TIME_INDEX_NAME, add_attr
import datetime


def test_aggr_per_second(translator):
    """
    select entity_type, entity_id, extract(YEAR from time_index) as ye, extract(MONTH from time_index) as mo, extract(DAY from time_index) as da, extract(HOUR from time_index) as ho, extract(MINUTE from time_index) as mi, extract(SECOND from time_index) as se, avg(attr_float) from et0 GROUP BY entity_type, entity_id, ye, mo, da, ho, mi, se limit 100;
    """
    return
    entities = create_random_entities(num_ids_per_type=2, num_updates=17)

    base_index = datetime.datetime(2016, 9, 1, 8, 0, 0)
    delta = datetime.timedelta(milliseconds=100)

    for i, e in enumerate(entities):
        t = base_index + i * delta
        e[TIME_INDEX_NAME] = t
        add_attr(e, 'attr_float', i)

    result = translator.insert(entities)
    assert result.rowcount == len(entities)

    translator._refresh([entities[0]['type']])

    # Query avg attr_float per second.
    res = translator.query(attr_names=['id', 'type', 'attr_float'],
                           aggr_method='avg',
                           aggr_period='second')
    assert len(res) == 2

    e0 = res[0]
    assert e0 == {
        'type': '0',
        'id': '0-0',
        'attr_float': {
            'values': [],
            'index': []
        }
    }

    e1 = res[1]
    assert e1 == {
        'type': '0',
        'id': '0-1',
        'attr_float': {
            'values': [],
            'index': []
        }
    }
