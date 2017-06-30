"""
Simple script that every SLEEP seconds:
    - Connects to STH_URL
    - Requests the Avg of the LAST_N temperature values of ENTITY_ID
    - Prints the Avg and the Response time of the requests
"""
from client.client import HEADERS
from utils.hosts import LOCAL
import json
import requests
import time
import timeit


SLEEP = 5
ENTITY_ID = 'Room1'
LAST_N = 10
STH_URL = 'http://{}:{}'.format(LOCAL, 8666)


def consume():
    url = '{}/STH/v1/contextEntities/type/Room/id/{}/attributes/temperature?&lastN={}'.format(
        STH_URL, ENTITY_ID, LAST_N
    )
    # aggrMethod=sum not working in comet :(
    r = requests.get(url, headers=HEADERS)
    assert r.ok, r.text

    data = json.loads(r.text)
    values = data['contextResponses'][0]['contextElement']['attributes'][0]['values']
    vals = [v['attrValue'] for v in values]
    avg = sum(vals) / float(LAST_N)
    return avg


if __name__ == '__main__':
    while True:
        avg = consume()
        res = timeit.timeit(consume, number=3, globals=globals())
        print("avg: {0:.2f}, rt: {1:.3f}".format(avg, res))
        time.sleep(SLEEP)
