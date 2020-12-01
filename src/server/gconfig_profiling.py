from cProfile import Profile
import multiprocessing
import server
from server.profiling import DurationSampler, DurationTable


bind = f"{server.DEFAULT_HOST}:{server.DEFAULT_PORT}"
workers = multiprocessing.cpu_count() * 4 + 1
worker_class = 'gthread'
threads = 1
loglevel = 'error'

profiling_dir = './profiling'
stats_file = profiling_dir + '/request_stats.txt'
sampler_dir = profiling_dir + '/sampler'
profiler_dir = profiling_dir + '/profiler'


def _profiler_file(worker_pid: int) -> str:
    return f"{profiler_dir}/profiler.{worker_pid}.data"


def _sampler_file(k) -> str:
    return f"{sampler_dir}/sampler.{k}.json"


def post_worker_init(worker):
    worker.duration_sampler = DurationSampler()

    worker.profiler = Profile()
    worker.profiler.enable()


def pre_request(worker, req):
    req.duration_sample_id = worker.duration_sampler.sample()


def post_request(worker, req, environ, resp):
    key = f"{req.path} [{req.method}]"
    worker.duration_sampler.collect(key, req.duration_sample_id)


def worker_exit(servo, worker):
    worker.duration_sampler.dump(_sampler_file(worker.pid))

    worker.profiler.disable()
    worker.profiler.dump_stats(_profiler_file(worker.pid))


def on_exit(servo):
    sampler_file_pattern = _sampler_file('*')
    t = DurationTable.from_files(sampler_file_pattern)
    t.write_stats(stats_file)
