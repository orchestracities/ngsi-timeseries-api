import logging
from utils.cfgreader import EnvReader, BoolVar
from flask_mqtt import Mqtt
import json
import requests

class MqttConfig:
    def __init__(self):
        pass

    def if_mqtt_enabled(self) -> bool:
        env_var = BoolVar('USE_MQTT', False)
        return EnvReader().safe_read(env_var)

def run_if_enabled(application, host, port, username, password, keepalive, tls, topic, ql_host, ql_port):
    application.config['MQTT_BROKER_URL'] = host
    application.config['MQTT_BROKER_PORT'] = port
    application.config['MQTT_USERNAME'] = username
    application.config['MQTT_PASSWORD'] = password
    application.config['MQTT_KEEPALIVE'] = keepalive
    application.config['MQTT_TLS_ENABLED'] = tls
    topic = topic

    mqtt_client = Mqtt(application)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    @mqtt_client.on_connect()
    def handle_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info('MQTT Connected successfully')
            mqtt_client.subscribe(topic) # subscribe topic
        else:
            logger.info('Bad connection. Code:', rc)

    @mqtt_client.on_message()
    def handle_mqtt_message(client, userdata, message):
        data = dict(
                topic=message.topic,
                payload=message.payload.decode()
            )
        logger.debug('Received message on topic: {topic} with payload: {payload}'.format(**data))
        try:
            payload = json.loads(message.payload)
        except ValueError:
            payload = None

        if payload:
            url = f'http://{ql_host}:{ql_port}/v2/notify'
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            r = requests.post(url, data=json.dumps(payload), headers=headers)
