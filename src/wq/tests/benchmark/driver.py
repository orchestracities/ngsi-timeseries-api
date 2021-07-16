from pathlib import Path
import shutil
from time import sleep

from tests.benchmark.driver_base import NOTIFY_TEST
from tests.benchmark.threaded_driver import ThreadedDriver
from utils.tests.docker import dir_from_file_path, DockerCompose
from wq.tests.benchmark.factory import new_row_count_sampler, DbType, \
    new_work_q_size_sampler


MONITORING_DIR_NAME = '_monitoring'
MAX_CLIENT_THREADS = 5
NOTIFY_REQUEST_N = 1000
DB_TABLE_FQN = 'public.etroom'    # mt.etroom when using Crate?


class TestScript:

    @staticmethod
    def this_files_dir() -> Path:
        return dir_from_file_path(__file__)

    @staticmethod
    def default_monitoring_dir() -> Path:
        return TestScript.this_files_dir() / MONITORING_DIR_NAME

    def __init__(self,
                 monitoring_dir_name: str = MONITORING_DIR_NAME,
                 max_client_threads: int = MAX_CLIENT_THREADS,
                 notify_request_n: int = NOTIFY_REQUEST_N,
                 db_backend: DbType = DbType.TIMESCALE,
                 db_table_fqn: str = DB_TABLE_FQN):
        self._base_dir = self.this_files_dir()
        self._mon_dir = self._base_dir / monitoring_dir_name
        self._docker = DockerCompose(__file__)
        self._max_client_threads = max_client_threads
        self._notify_request_n = notify_request_n
        self._db_backend = db_backend
        self._db_table_fqn = db_table_fqn
        self._db_sampler = None
        self._q_sampler = None

    def _prep_monitoring_dir(self):
        if self._mon_dir.exists():
            shutil.rmtree(self._mon_dir)
        self._mon_dir.mkdir(parents=True)

    def _start_docker_and_wait_for_services(self):
        self._docker.start()
        sleep(10)
        # TODO call QL's version endpoint rather than sleeping.
        # If it's up, then Redis & DB backend are up to b/c of docker deps.

    def _start_samplers(self):
        self._db_sampler = new_row_count_sampler(self._mon_dir,
                                                 self._db_backend,
                                                 self._db_table_fqn,
                                                 self._notify_request_n)  # (*)
        self._q_sampler = new_work_q_size_sampler(self._mon_dir)
        self._q_sampler.start()
        self._db_sampler.start()
# NOTE. Deadlock.
# The DB sampler will stop after counting `notify_request_n`. At that point
# we kill the q sampler and exit. But if there are insert errors or any other
# kind of error that results in less than `notify_request_n` winding up in
# the table, then we get stuck waiting forever!

    def _collect_telemetry_data(self):
        self._db_sampler.join()    # (*)
        self._q_sampler.kill()
        self._q_sampler.join()
# NOTE. Deadlock. See above note about it.

    def _send_notify_requests(self):
        workers = ThreadedDriver(max_workers=self._max_client_threads,
                                 requests_number=self._notify_request_n,
                                 monitoring_dir=str(self._mon_dir))
        workers.run(test_id=NOTIFY_TEST)

    def main(self, with_docker=True):
        self._prep_monitoring_dir()
        if with_docker:
            self._docker.build_images()
            self._start_docker_and_wait_for_services()

        self._start_samplers()
        self._send_notify_requests()
        self._collect_telemetry_data()

        if with_docker:
            self._docker.stop()
