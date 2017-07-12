import time
import json


def subscribe(orion, subscription):
    """
    :param OrionClient orion:
    :param dict subscription: subscription to be done (using NGSI v2)
    :return: str the id of the generated subscription
    """
    r = orion.subscribe(subscription)
    assert r.ok, r.text

    r = orion.get('subscriptions')
    assert r.ok
    assert r.status_code == 200

    subscription_id = json.loads(r.text)[0]
    return subscription_id



def sense(orion, entity, update_callback, sleep):
    """
    :param OrionClient orion:
    :param dict entity: NGSI JSON representation
    :param callable update_callback: function that returns the dict to be passe to the entity update calls.
    :param float sleep: seconds to sleep between consecutive updates.
    """
    r = orion.insert(entity)
    assert r.ok, r.text
    print('Inserted: {}'.format(entity))

    try:
        while True:
            time.sleep(sleep)
            args = update_callback()
            r = orion.update(entity['id'], args)
            assert r.ok, r.text
            print('Updated: {}'.format(args))

    finally:
        r = orion.delete(entity['id'])
        assert r.ok, r.text

