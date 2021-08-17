import pytest
import os
import time
import timeit

from conftest import REDIS_PORT


@pytest.fixture(scope='module')
def docker_redis(docker_services):
    os.environ['PATH'] += os.pathsep + "/usr/local/bin"
    docker_services.start('redis')
