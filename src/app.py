from utils.hosts import LOCAL
from flask_cors import CORS
import os


def configure_cors(app, origin):
    # using a similar convention as the Orion context broker:
    # https://fiware-orion.readthedocs.io/en/master/user/cors/index.html
    if origin.upper() == "__ALL":
        origin = "*"
    headers = os.environ.get("QL_CORS_ALLOWED_HEADERS", "*")
    max_age = os.environ.get("QL_CORS_MAX_AGE", "86400")  # in s
    expose_headers = os.environ.get("QL_CORS_EXPOSE_HEADERS", None)
    resources = {r"/v2/*": {"origins": origin, "headers": headers, "max_age": max_age, expose_headers: expose_headers}}
    CORS(app.app, resource=resources)


if __name__ == '__main__':
    import connexion

    app = connexion.FlaskApp(__name__, specification_dir='../specification/')
    app.add_api('quantumleap.yml',
                arguments={'title': 'QuantumLeap V2 API'},
                pythonic_params=True,
                # validate_responses=True, strict_validation=True
                )
    cors_allowed_origin = os.environ.get('QL_CORS_ALLOWED_ORIGIN', None)
    if cors_allowed_origin:
        configure_cors(app, cors_allowed_origin)
    app.run(host=LOCAL, port=8668)
