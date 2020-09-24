from connexion import FlaskApp
import logging
import server


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
