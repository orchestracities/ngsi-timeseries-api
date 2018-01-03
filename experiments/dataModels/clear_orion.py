import os
import requests
import sys

# INPUT
ORION_HOST = os.environ.get('ORION_HOST', '0.0.0.0')
ORION_PORT = os.environ.get('ORION_PORT', '1026')
ORION_URL = 'http://{}:{}'.format(ORION_HOST, ORION_PORT)

# INTERNAL
HEADERS = {
    'Fiware-Service': 'default',
    'Fiware-ServicePath': '/',
}
HEADERS_PUT = HEADERS.copy()
HEADERS_PUT['Content-Type'] = 'application/json'


if __name__ == '__main__':
    # Confirm deletion
    msg = "Remove all subscriptions and entities in ORION {}? [y/N] "
    print(msg.format(ORION_URL))
    if sys.stdin.read(1) != 'y':
        print("Exiting without deleting anything.")
        sys.exit(0)

    # Clean subscriptions
    subs = requests.get('{}/v2/subscriptions'.format(ORION_URL),
                        headers=HEADERS).json()
    for s in subs:
        requests.delete('{}/v2/subscriptions/{}'.format(ORION_URL, s['id']),
                        headers=HEADERS)
    print("removed {} subscriptions.".format(len(subs)))

    # Clean entities
    entities = requests.get('{}/v2/entities?attrs=null'.format(ORION_URL),
                            headers=HEADERS).json()
    for e in entities:
        url = '{}/v2/entities/{}?type={}'
        requests.delete(url.format(ORION_URL, e['id'], e['type']),
                        headers=HEADERS)
    print("removed {} entities.".format(len(entities)))
