import sys
from typing import Dict, Iterable, Union

import server.telemetry.monitor as monitor

REQUESTS_N = 10000
QL_BASE_URL = 'http://localhost:8668'
VERSION_TEST = 'version'
NOTIFY_TEST = 'notify'

MONITORING_DIR = '_monitoring'
# NOTE. Shared monitoring dir. Out of convenience, we use the same dir as
# QuantumLeap so the analysis script can import both client and server
# data in the same Pandas frame.


def setup_monitor(monitoring_dir: str):
    monitor.start(monitoring_dir=monitoring_dir,
                  with_runtime=False,  # (*)
                  with_profiler=False)
# NOTE. Shared monitoring dir. Because of that, we can't collect runtime
# metrics since the series would have the same names as the server-side
# series and we wouldn't be able to tell them apart. If we do need client
# runtime stats, we should use a separate monitoring directory.


def version_url() -> str:
    return f"{QL_BASE_URL}/version"


def notify_url() -> str:
    return f"{QL_BASE_URL}/v2/notify"


def notify_entity() -> dict:
    return {
        "data": [
            {
                "id": "Room:1",
                "type": "Room",
                "temperature": {
                    "value": 23.3,
                    "type": "Number"
                },
                "pressure": {
                    "value": 720,
                    "type": "Integer"
                }
            }
        ]
    }


HttpResponseCode = int
Result = Union[HttpResponseCode, Exception]
TestRunResults = Iterable[Result]


def responses_by_code_count(rs: TestRunResults) -> Dict[HttpResponseCode, int]:
    d = {}
    codes = [r for r in rs if isinstance(r, int)]
    for k in codes:
        cnt = d.get(k, 0)
        d[k] = cnt + 1
    return d


def print_test_results(rs: TestRunResults):
    xs = list(rs)
    exs = [x for x in xs if isinstance(x, Exception)]
    for e in exs:
        print(e)
    print(f">>> {len(exs)} exception(s) occurred.")

    print(f">>> HTTP response count by status code:")
    for code, count in responses_by_code_count(xs).items():
        print(f"HTTP {code}: {count}")


class Driver:

    def __init__(self, monitoring_dir: str = MONITORING_DIR):
        self._mon_dir = monitoring_dir

    def _do_run(self, test_id: str) -> TestRunResults:
        pass

    def run(self, test_id: str):
        setup_monitor(self._mon_dir)

        sample_id = monitor.start_duration_sample()
        rs = self._do_run(test_id)
        monitor.stop_duration_sample('client: cumulative time', sample_id)

        monitor.stop()
        print_test_results(rs)

    def main(self):
        try:
            arg = sys.argv[1]
            if arg not in (VERSION_TEST, NOTIFY_TEST):
                raise IndexError()
            self.run(arg)
        except IndexError:
            raise SystemExit(
                f"Usage: {sys.argv[0]} {VERSION_TEST}|{NOTIFY_TEST}")
