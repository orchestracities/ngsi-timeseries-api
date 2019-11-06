import json
import random
import requests


# QL_HOST = os.environ.get('QL_HOST', "quantumleap")
QL_HOST = "localhost"
QL_PORT = 8668
QL_URL = f"http://{QL_HOST}:{QL_PORT}/v2"


def gen_entity(entity_id, entity_type):
    return {
        'id': entity_id,
        'type': entity_type,
        'a_number': {
            'type': 'Number',
            'value': 50 * random.uniform(0, 1)
        },
        'an_integer': {
            'type': 'Integer',
            'value': 50
        },
        'a_bool': {
            'type': 'Boolean',
            'value': 'true'
        },
        'a_datetime': {
            'type': 'DateTime',
            'value': '2018-01-01T11:46:45.{}Z'.format(random.randint(0, 99))
        },
        'a_point': {
            'type': 'geo:point',
            'value': '2, 1'
        },
        'a_text': {
            'value': 'no type => text'
        },
        'an_obj': {
            'type': 'Custom',
            'value': {
                'h': 'unknown type && dict value => structured value'
            }
        },
        'an_array': {
            'type': 'StructuredValue',
            'value': [1, 'struct val but array =>', 2, 'array of str']
        }
    }


def gen_notification(entities):
    return {
        'subscriptionId': str(random.randint(1, 2**64)),
        'data': entities
    }


def post_notification(payload, fw_svc=None, fw_path=None):
    url = f"{QL_URL}/v2/notify"

    headers = {'Content-Type': 'application/json'}
    if fw_svc:
        headers.update({'fiware-service': fw_svc})
    if fw_path:
        headers.update({'fiware-servicepath': fw_path})

    body = json.dumps(payload)

    return requests.post(url, headers=headers, data=body)


def test_simple_notification():
    entities = [gen_entity('td:1', 'test-device')]
    msg = gen_notification(entities)
    post_notification(msg)


def test_simple_notification_with_fw_params():
    entities = [gen_entity('td:2', 'test-device')]
    msg = gen_notification(entities)
    post_notification(msg, fw_svc="tenant", fw_path="/devices")
