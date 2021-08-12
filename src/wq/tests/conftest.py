import os
import pytest
from time import sleep

from translators.factory import QL_DEFAULT_DB_ENV_VAR, TIMESCALE_BACKEND
from translators.timescale import postgres_translator_instance
from utils.tests.docker import DockerCompose
from wq.core.cfg import OFFLOAD_WORK_VAR


TIMESCALE_SVC_NAME = 'timescale'
WQ_SVC_NAME = 'quantumleap-wq'

docker = DockerCompose(__file__)


@pytest.fixture(scope='session', autouse=True)
def build_images():
    docker.build_images()


@pytest.fixture(scope='package', autouse=True)
def run_services():
    docker.start()
    wait_for_timescale()
    yield
    docker.stop()


def start_timescale():
    docker.start_service(TIMESCALE_SVC_NAME)


def stop_timescale():
    docker.stop_service(TIMESCALE_SVC_NAME)


def wait_for_timescale(max_wait: float = 10.0, sleep_interval: float = 0.5):
    time_left_to_wait = max_wait
    while time_left_to_wait > 0:
        try:
            with postgres_translator_instance():
                return
        except BaseException:
            time_left_to_wait -= sleep_interval
            sleep(sleep_interval)
    assert False, f"waited longer than {max_wait} secs for timescale!"


def pause_wq():
    docker.pause_service(WQ_SVC_NAME)


def resume_wq():
    docker.unpause_service(WQ_SVC_NAME)


@pytest.fixture(scope='session', autouse=True)
def set_env_vars():
    os.environ[OFFLOAD_WORK_VAR.name] = 'true'
    os.environ[QL_DEFAULT_DB_ENV_VAR] = TIMESCALE_BACKEND
