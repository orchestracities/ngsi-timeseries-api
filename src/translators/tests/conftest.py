import pytest
import os
from six.moves.urllib.error import HTTPError
from six.moves.urllib.request import urlopen


def check_crate(docker_ip, public_port):
    """Check if a crate is reachable.

    Makes a simple GET request to path of the HTTP endpoint. Service is
    available if returned status code is < 500.
    """
    url = 'http://{}:{}'.format(docker_ip, public_port)
    try:
        r = urlopen(url)
        return r.code < 500
    except HTTPError as e:
        # If service returns e.g. a 404 it's ok
        return e.code < 500
    except Exception:
        # Possible service not yet started
        return False


@pytest.fixture(autouse=True, scope='package')
def docker_stack(docker_services):
    os.environ['PATH'] += os.pathsep + "/usr/local/bin"
    docker_services.start('crate')
    docker_services.start('timescale')
    docker_services.start('redis')
    docker_services.start('quantumleap-db-setup')
    docker_services.wait_for_service(
         "crate",
         4200,
         check_server=check_crate,
    )
