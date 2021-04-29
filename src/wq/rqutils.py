from enum import Enum

from rq.job import Job, JobStatus

from wq.cfg import redis_connection
from wq.task import TaskId


# TODO scalability.
# 1. Use streaming instead of sucking whole data sets into memory.
# 2. Query Redis instead of filtering jobs or/and use RQ's job registries.
# Notice the approach below should work decently as long queries are narrow
# (which is the case at the moment but may change in the future) and a few
# thousand messages ever sit in the error or processed queues at any given
# time---maybe a fair assumption for small scale ops or if TTLs are short,
# but in general it'd be better to have a solution that works at scale.


class TaskStatus(Enum):
    PENDING = 1
    SUCCEEDED = 2
    FAILED = 3
    UNKNOWN = 4

    @staticmethod
    def from_job_status(s: JobStatus) -> 'TaskStatus':
        if s in (JobStatus.QUEUED, JobStatus.STARTED,
                 JobStatus.DEFERRED, JobStatus.SCHEDULED):
            return TaskStatus.PENDING
        if s == JobStatus.FINISHED:
            return TaskStatus.SUCCEEDED
        if s == JobStatus.FAILED:
            return TaskStatus.FAILED
        return TaskStatus.UNKNOWN


def find_jobs(rq_key_matcher: str) -> [Job]:
    redis = redis_connection()
    ks = redis.keys(rq_key_matcher)
    ids = [TaskId.id_repr_from_rq_key(k.decode('utf-8')) for k in ks]
    js = Job.fetch_many(job_ids=ids, connection=redis)
    return [j for j in js if js is not None]
# NOTE. it could happen that i is in ids but the job is deleted forever b/c
# of an expired TTL just before we fetch js. fetch_many puts a None in the
# returned list if it could find no job having an id of i. Have a look at
# the code.


def find_jobs_in_status(rq_key_matcher: str, status: TaskStatus) -> [Job]:
    def is_in_status(job: Job, s: TaskStatus):
        job_s = job.get_status()
        return TaskStatus.from_job_status(job_s) == s

    js = find_jobs(rq_key_matcher)
    return [j for j in js if is_in_status(j, status)]


def find_pending_jobs(rq_key_matcher: str) -> [Job]:
    return find_jobs_in_status(rq_key_matcher, TaskStatus.PENDING)


def find_successful_jobs(rq_key_matcher: str) -> [Job]:
    return find_jobs_in_status(rq_key_matcher, TaskStatus.SUCCEEDED)


def find_failed_jobs(rq_key_matcher: str) -> [Job]:
    return find_jobs_in_status(rq_key_matcher, TaskStatus.FAILED)


def delete_jobs(rq_key_matcher: str):
    ts = find_jobs(rq_key_matcher)
    for t in ts:
        t.delete()

