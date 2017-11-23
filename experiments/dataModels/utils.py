import json
import requests
import time


# INTERNAL
HEADERS = {
    'Fiware-Service': 'default',
    'Fiware-ServicePath': '/',
}
HEADERS_PUT = HEADERS.copy()
HEADERS_PUT['Content-Type'] = 'application/json'

COORDS = [
        [51.235170, 4.421283],
        [51.233103, 4.423617],
        [51.257595, 4.432838],
        [51.260580, 4.426038],
        [51.208525, 4.437985],
        [51.210266, 4.425305],
        [51.204714, 4.416675],
        [51.208948, 4.418556],
        [51.217179, 4.341202],
        [51.218305, 4.336690],
    ]


def insert_entities(entities, sleep, orion_url):
    for e in entities:
        time.sleep(sleep)
        url = '{}/v2/entities?options=keyValues'.format(orion_url)
        r = requests.post(url, data=json.dumps(e), headers=HEADERS_PUT)
        if not r.ok:
            if "Already Exists" in r.text:
                print("Already exists: {}".format(e['id']))
                continue
            raise RuntimeError(r.text)
        print("Inserted: {}".format(json.dumps(e)))


def update_entity(entity, attrs_to_update, orion_url):
    url = '{}/v2/entities/{}/attrs'.format(orion_url, entity['id'])
    r = requests.patch(url, data=json.dumps(attrs_to_update),
                       headers=HEADERS_PUT)
    if not r.ok:
        raise RuntimeError(r.text)
    print("Updated {} with {}".format(entity['id'], attrs_to_update))
