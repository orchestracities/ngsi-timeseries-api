from utils import HEADERS_PUT
from locust import HttpLocust, TaskSet, task
import json
import os
import random

# INPUT (via environment variables)
ORION_URL = os.environ.get('ORION_URL', 'http://0.0.0.0:1026')
MIN_WAIT = os.environ.get('MIN_WAIT', 1000)
MAX_WAIT = os.environ.get('MAX_WAIT', 3000)


class DataModelsTaskSet(TaskSet):

    def on_start(self):
        """
        on_start is called when a Locust start before any task is scheduled
        """
        self.trafic_flow_observers = 0
        self.insert_traffic_flow_observed()

        self.air_quality_observers = 0
        self.insert_air_quality_observed()

    @task(1)
    def insert_traffic_flow_observed(self):
        from traffic_flow_observer import create_entity

        entity_id = 'traffic_flow_observer_{}'
        e = create_entity(entity_id.format(self.trafic_flow_observers))
        data = json.dumps(e)
        url = "/v2/entities?options=keyValues"

        self.client.post(url, data=data, headers=HEADERS_PUT)
        self.trafic_flow_observers += 1

    @task(1000)
    def update_traffic_flow_observed(self):
        from traffic_flow_observer import get_attrs_to_update

        e = int(random.random() * self.trafic_flow_observers)
        entity_id = 'traffic_flow_observer_{}'.format(e)
        attrs = get_attrs_to_update()

        data = json.dumps(attrs)
        url = "/v2/entities/{}/attrs".format(entity_id)
        self.client.patch(url, data=data, headers=HEADERS_PUT)

    @task(1)
    def insert_air_quality_observed(self):
        from air_quality_observer import create_entity

        entity_id = 'air_quality_observer_{}'
        e = create_entity(entity_id.format(self.air_quality_observers))
        data = json.dumps(e)
        url = "/v2/entities?options=keyValues"

        self.client.post(url, data=data, headers=HEADERS_PUT)
        self.air_quality_observers += 1

    @task(1000)
    def update_air_quality_observed(self):
        from air_quality_observer import get_attrs_to_update

        e = int(random.random() * self.air_quality_observers)
        entity_id = 'air_quality_observer_{}'.format(e)
        attrs = get_attrs_to_update()

        data = json.dumps(attrs)
        url = "/v2/entities/{}/attrs".format(entity_id)
        self.client.patch(url, data=data, headers=HEADERS_PUT)


class DataModelsLocust(HttpLocust):
    task_set = DataModelsTaskSet
    host = ORION_URL
    min_wait = MIN_WAIT
    max_wait = MAX_WAIT
