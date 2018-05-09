import requests
import json


HEADERS = {
}
HEADERS_PUT = HEADERS.copy()
HEADERS_PUT['Content-Type'] = 'application/json'


class OrionClient(object):
    """
    Simple python client to interact with FIWARE Context Broker (Orion).

    Its API will start oversimplified and will evolve with use. This will help in defining the controller for a swagger
    specification of the API at a later point.
    """

    def __init__(self, host, port=1026):
        """
        :param host: Host name where Context Broker is running
        :param port: Port where Context Broker is available. Defaults to 1026
        """
        self.url = 'http://{}:{}'.format(host, port)


    def version(self):
        r = requests.get('{}/version'.format(self.url))
        return r


    def subscribe(self, subscription):
        r = requests.post('{}/v2/subscriptions'.format(self.url), data=json.dumps(subscription), headers=HEADERS_PUT)
        return r


    def unsubscribe(self, subscription_id):
        r = requests.delete('{}/v2/subscriptions/{}'.format(self.url, subscription_id), headers=HEADERS)
        return r


    def subscribe_v1(self, subscription):
        r = requests.post('{}/v1/subscribeContext'.format(self.url), data=json.dumps(subscription), headers=HEADERS_PUT)
        return r


    def insert(self, entity):
        r = requests.post('{}/v2/entities'.format(self.url), data=json.dumps(entity), headers=HEADERS_PUT)
        return r


    def update(self, entity_id, attrs):
        r = requests.patch('{}/v2/entities/{}/attrs'.format(self.url, entity_id), data=json.dumps(attrs),
                           headers=HEADERS_PUT)
        return r


    def get(self, suffix):
        r = requests.get('{}/v2/{}'.format(self.url, suffix), headers=HEADERS)
        return r


    def delete(self, entity_id):
        r = requests.delete('{}/v2/entities/{}'.format(self.url, entity_id), headers=HEADERS)
        return r
