import server.wsgi as flask
import server.grunner as gunicorn
from flask import has_request_context, request
from utils.cfgreader import EnvReader, BoolVar, StrVar
import logging
from flask.logging import default_handler


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.corr = request.headers.get('fiware_correlator', None)
            record.remote_addr = request.remote_addr
            record.srv = request.headers.get('fiware-service', None)
            if record.srv:
                record.subserv = request.headers.get(
                    'fiware-servicepath', '/')
            else:
                record.subserv = '/'
            if len(request.data) > 0 and request.json and request.json['data']:
                record.payload = request.json['data']
            else:
                record.payload = None
        else:
            record.corr = None
            record.remote_addr = None
            record.srv = None
            record.subserv = None
            record.payload = None

        return super().format(record)


formatter = RequestFormatter(
    'time=%(asctime)s.%(msecs)03d | '
    'level=%(levelname)s | corr=%(corr)s | from=%(remote_addr)s | '
    'srv=%(srv)s | subserv=%(subserv)s | op=%(funcName)s | comp=%(name)s | '
    'msg=%(message)s | payload=%(payload)s | '
    'thread=%(thread)d  | process=%(process)d',
    datefmt='%Y-%m-%d %I:%M:%S'
)

default_handler.setFormatter(formatter)


def use_flask() -> bool:
    env_var = BoolVar('USE_FLASK', False)
    return EnvReader().safe_read(env_var)


def setup():
    r = EnvReader(log=logging.getLogger().debug)
    level = r.read(StrVar('LOGLEVEL', 'INFO')).upper()
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(default_handler)


if __name__ == '__main__':
    setup()
    if use_flask():  # dev mode, run the WSGI app in Flask dev server
        flask.run()
    else:            # prod mode, run the WSGI app in Gunicorn
        gunicorn.run()
