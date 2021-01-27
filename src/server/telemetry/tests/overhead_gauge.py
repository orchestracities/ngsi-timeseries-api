import os
import resource
import time

import server.telemetry.monitor as monitor


monitoring_on = True
monitoring_dir = '_monitoring'
loops = 500
delay = 0.05

start_time = time.perf_counter()


def init():
    os.makedirs(monitoring_dir, exist_ok=True)
    monitor.start(monitoring_dir=monitoring_dir,
                  with_gc_sampler=False,
                  with_profiler=False)


def do_work():
    time.sleep(delay)


def run_bare():
    for _ in range(loops):
        do_work()


def run_with_monitoring():
    for _ in range(loops):
        sample_id = monitor.start_duration_sample()
        do_work()
        monitor.stop_duration_sample('test', sample_id)


def print_readings():
    me = resource.getrusage(resource.RUSAGE_SELF)
    elapsed = time.perf_counter() - start_time

    print(f"Time (seconds): {elapsed}")
    print(f"Max RSS (kB on Linux | bytes on MacOS): {me.ru_maxrss}")


if __name__ == "__main__":
    if monitoring_on:
        init()
        run_with_monitoring()
        monitor.stop()
    else:
        run_bare()

    print_readings()
