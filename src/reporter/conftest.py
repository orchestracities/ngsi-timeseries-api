import pytest
import random


def create_notification(entity_type='Room', entity_id='Room1', subs_id=None):
    subs_id = subs_id or '5947d174793fe6f7eb5e3961'
    t = random.randint(0, 99)
    return {
        'subscriptionId': subs_id,
        'data': [
            {
                'id': entity_id,
                'type': entity_type,
                'temperature': {
                    'type': 'Number',
                    'value': 50 * random.uniform(0, 1),
                    'metadata': {
                        'dateModified': {
                            'type': 'DateTime',
                            'value': '2018-01-01T11:46:45.{}Z'.format(t)
                        }
                    }
                }
            }
        ]
    }


@pytest.fixture
def notification():
    return create_notification()
