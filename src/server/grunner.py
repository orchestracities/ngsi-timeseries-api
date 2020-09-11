import sys
from typing import Any, Dict

from gunicorn.app.base import Application
from gunicorn.config import make_settings

import server.gconfig
from server.wsgi import application


def quantumleap_base_config() -> Dict[str, Any]:
    """
    Read the base QuantumLeap configuration from the ``server.gconfig``
    module.

    :return: the dictionary with the base QuantumLeap settings.
    """
    gunicorn_setting_names = [k for k, v in make_settings().items()]
    server_config_vars = vars(server.gconfig).items()
    return {
        k: v
        for k, v in server_config_vars if k in gunicorn_setting_names
    }


class GuantumLeap(Application):
    """
    Gunicorn server runner.

    This class is a fully-fledged Gunicorn server WSGI runner, just like
    ``WSGIApplication`` from ``gunicorn.app.wsgiapp``, except the WSGI
    app to run is fixed (QuantumLeap) and the content of ``server.gconfig``
    is used as initial configuration. Notice you can override these base
    config settings using CLI args or/and a config file as you'd normally
    do with Gunicorn, but you can't run any WSGI app other than QuantumLeap.
    """

    def init(self, parser, opts, args):
        return quantumleap_base_config()

    def load(self):
        return application


def run():
    """
    Start a fully-fledged Gunicorn server to run QuantumLeap.

    If you pass no CLI args, this is the same as running

    ``$ gunicorn server.wsgi --config server/gconfig.py``

    which starts Gunicorn to run the QuantumLeap WSGI Flask app with
    the Gunicorn settings in our ``server.gconfig`` module.
    You can specify any valid Gunicorn CLI option and it'll take
    precedence over any setting with the same name in ``server.gconfig``.
    Also you can specify a different config module and options in that
    module will override those with the same name in ``server.gconfig``.
    The only thing you won't be able to change is the WSGI app to run,
    QuantumLeap.
    """
    gunicorn = GuantumLeap('%(prog)s [OPTIONS] [APP_MODULE]')  # (1)
    sys.argv[0] = 'quantumleap'                                # (2)
    sys.exit(gunicorn.run())                                   # (2)

# NOTE.
# 1. We keep the same usage as in `gunicorn.app.wsgiapp.run`.
# 2. We basically start Gunicorn in the same way as the Gunicorn launcher
# would:
#
# $ cat $(which gunicorn)
#
# #!/Users/andrea/.local/share/virtualenvs/ngsi-timeseries-api-MeJ80LMF/bin/python
# # -*- coding: utf-8 -*-
# import re
# import sys
# from gunicorn.app.wsgiapp import run
# if __name__ == '__main__':
#     sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
#     sys.exit(run())
#
