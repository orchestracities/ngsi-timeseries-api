from concurrent.futures import ThreadPoolExecutor
import requests
import threading
from typing import Callable

from tests.benchmark.driver_base import *


MAX_THREAD_WORKERS = 5


thread_local = threading.local()


def get_session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


TestTask = Callable[[int], Result]


def with_session(test_label: str,
                 do: Callable[[requests.Session],
                              requests.Response]) -> Result:
    try:
        sample_id = monitor.start_duration_sample()
        with do(get_session()) as response:
            label = f"client:{test_label}:{response.status_code}"
            monitor.stop_duration_sample(label, sample_id)
            return response.status_code
    except Exception as e:
        return e
        # don't time exceptions


def run_notify_test(request_number: int) -> Result:
    return with_session(
        test_label=NOTIFY_TEST,
        do=lambda s: s.post(notify_url(), json=notify_entity()))


def run_version_test(request_number: int) -> Result:
    return with_session(
        test_label=VERSION_TEST,
        do=lambda s: s.get(version_url()))

# NOTE. Request number. Not used at the moment, but we could use it in the
# future for request tracing in case we'll ever need more accurate, per-request,
# individual measurements. In that case, both server and client would label
# durations using the request number so then when analysing the data we can
# tell exactly, for each request, how much time was spent where.


def lookup_test_task(test_id: str) -> TestTask:
    tasks = {
        VERSION_TEST: run_version_test,
        NOTIFY_TEST: run_notify_test
    }
    return tasks[test_id]


class ThreadedDriver(Driver):

    def __init__(self,
                 max_workers: int = MAX_THREAD_WORKERS,
                 requests_number: int = REQUESTS_N,
                 monitoring_dir: str = MONITORING_DIR):
        super().__init__(monitoring_dir=monitoring_dir)
        self._max_workers = max_workers
        self._request_n = requests_number

    def _do_run(self, test_id: str) -> TestRunResults:
        test_task = lookup_test_task(test_id)
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            return executor.map(test_task, range(self._request_n))


if __name__ == "__main__":
    ThreadedDriver().main()
