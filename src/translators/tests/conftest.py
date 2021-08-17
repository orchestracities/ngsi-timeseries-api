import pytest
import os

@pytest.fixture(autouse=True, scope='package')
def docker_stack(docker_services):
    os.environ['PATH'] += os.pathsep + "/usr/local/bin"
    docker_services.start('crate')
    docker_services.start('timescale')
    docker_services.start('redis')
    docker_services.start('quantumleap-db-setup')
