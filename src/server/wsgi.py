from connexion import FlaskApp
import logging
import server
from utils.cfgreader import EnvReader, BoolVar
from flask.logging import default_handler


SPEC_DIR = '../../specification/'
SPEC = 'quantumleap.yml'


def new_wrapper() -> FlaskApp:
    """
    Factory function to build a Connexion wrapper to manage the Flask
    application in which QuantumLeap runs.

    :return: the Connexion wrapper.
    """
    wrapper = FlaskApp(__name__,
                       specification_dir=SPEC_DIR)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    wrapper.add_api(SPEC,
                    arguments={'title': 'QuantumLeap V2 API'},
                    pythonic_params=True,
                    # validate_responses=True, strict_validation=True
                    )
    return wrapper


quantumleap = new_wrapper()
"""
Singleton Connexion wrapper that manages the QuantumLeap Flask app.
"""

application = quantumleap.app

def use_mqtt() -> bool:
    env_var = BoolVar('USE_MQTT', False)
    print(EnvReader().safe_read(env_var))
    return EnvReader().safe_read(env_var)

if use_mqtt():
    application.config['MQTT_BROKER_URL'] = server.MQTT_HOST
    application.config['MQTT_BROKER_PORT'] = server.MQTT_PORT
    application.config['MQTT_USERNAME'] = server.MQTT_USERNAME
    application.config['MQTT_PASSWORD'] = server.MQTT_PASSWORD
    application.config['MQTT_KEEPALIVE'] = server.MQTT_KEEPALIVE
    application.config['MQTT_TLS_ENABLED'] = server.MQTT_TLS_ENABLED
    topic = server.MQTT_TOPIC

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
            url = f'http://{server.DEFAULT_HOST}:{server.DEFAULT_PORT}/v2/notify'
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            r = requests.post(url, data=json.dumps(payload), headers=headers)


"""
The WSGI callable to run QuantumLeap in a WSGI container of your choice,
e.g. Gunicorn, uWSGI.
Notice that Gunicorn will look for a WSGI callable named `application` if
no variable name follows the module name given on the command line. So one
way to run QuantumLeap in Gunicorn would be

    gunicorn server.wsgi --config server/gconfig.py

An even more convenient way is to use our Gunicorn standalone server,
see `server.grunner` module.
"""


def run():
    """
    Runs the bare-bones QuantumLeap WSGI app.
    Notice the app will run in the Flask dev server, so it's only good
    for development, not prod!
    """
    quantumleap.run(host=server.DEFAULT_HOST,
                    port=server.DEFAULT_PORT)
