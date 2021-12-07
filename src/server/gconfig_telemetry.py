import multiprocessing
import os
import server
import server.telemetry.monitor as monitor


bind = f"{server.DEFAULT_HOST}:{server.DEFAULT_PORT}"
workers = os.getenv('WORKERS', 2)
worker_class = 'gthread'
threads = os.getenv('THREADS', 1)
loglevel = 'error'


monitoring_dir = '_monitoring'


def post_worker_init(worker):
    os.makedirs(monitoring_dir, exist_ok=True)
    monitor.start(monitoring_dir=monitoring_dir,
                  with_runtime=True,
                  with_profiler=False)


def pre_request(worker, req):
    req.duration_sample_id = monitor.start_duration_sample()


def post_request(worker, req, environ, resp):
    key = f"{req.path} [{req.method}]"
    monitor.stop_duration_sample(key, req.duration_sample_id)


def worker_exit(servo, worker):
    monitor.stop()
