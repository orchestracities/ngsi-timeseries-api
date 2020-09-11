import server.wsgi as flask
import server.grunner as gunicorn
from utils.cfgreader import EnvReader, BoolVar


def use_flask() -> bool:
    env_var = BoolVar('USE_FLASK', False)
    return EnvReader().safe_read(env_var)


if __name__ == '__main__':
    if use_flask():  # dev mode, run the WSGI app in Flask dev server
        flask.run()
    else:            # prod mode, run the WSGI app in Gunicorn
        gunicorn.run()
