from itertools import chain
from typing import Iterable

from rq import Queue
from rq.job import Job

from utils.itersplit import IterCostSplitter
from wq.core.cfg import redis_connection


RQ_JOB_KEY_PREFIX = Job.redis_job_namespace_prefix
"""
The prefix RQ puts in front of a job ID to build the corresponding
Redis key for storing the job data in a hash.
"""

RqJobKey = str
RqJobId = str


def job_id_to_job_key(jid: RqJobId) -> RqJobKey:
    """
    Build an RQ key for the given RQ job ID.

    :param jid: the job ID. Must not be ``None``.
    :return: the Redis key RQ uses to identify the job having an ID of
        ``jid``.

    Examples:

        >>> job_id_to_job_key('my:jobbie')
        'rq:job:my:jobbie'
    """
    if jid is None:
        raise ValueError

    return f"{RQ_JOB_KEY_PREFIX}{jid}"
# NOTE.
# Not using RQ's own ``Job.key_for`` since it returns bytes instead of str.


def job_id_from_job_key(k: RqJobKey) -> RqJobId:
    """
    Extract the RQ job ID from its RQ job key.

    :param k: a valid RQ job key. Must not be ``None``.
    :return: the RQ job ID part of the key.

    Examples:

        >>> job_id_from_job_key('rq:job:my:jobbie')
        'my:jobbie'

        >>> k = job_id_to_job_key('my:jobbie')
        >>> job_id_from_job_key(k)
        'my:jobbie'
    """
    if k is None:
        raise ValueError

    if k.startswith(RQ_JOB_KEY_PREFIX):
        return k[len(RQ_JOB_KEY_PREFIX):]
    return ''


def job_key_matcher(jid_pattern: str) -> str:
    """
    Build a Redis expression to pick any RQ job key having a job ID
    part matching the input pattern.

    :param jid_pattern: a Redis pattern to match an RQ job ID.
         Must not be ``None``.
    :return: the RQ key pattern.

    Examples:

        >>> job_key_matcher('my:jo?bie')
        'rq:job:my:jo?bie'
    """
    return job_id_to_job_key(jid_pattern)


def starts_with_matcher(prefix: str) -> str:
    """
    Build a Redis expression to match any string beginning with the given
    ``prefix``.

    :param prefix: the string initial segment to match. Must not be ``None``.
    :return: a Redis pattern.

    Examples:

        >>> starts_with_matcher('my:')
        'my:*'
    """
    if prefix is None:
        raise ValueError
    return f"{prefix}*"


def find_job_keys(job_id_matcher: str) -> Iterable[RqJobKey]:
    """
    Iterate the RQ job keys having a job ID part matching the given Redis
    expression.

    :param job_id_matcher: a Redis pattern to match the job ID part of an
        RQ job key.
    :return: an generator object to iterate the matching keys.
    """
    key_matcher = job_key_matcher(job_id_matcher)
    redis = redis_connection()
    for k in redis.scan_iter(match=key_matcher):
        yield k.decode('utf-8')    # (*)
# NOTE.
# This is only meaningful when the Redis key was a Python string originally,
# which is the case if you're matching 'rq:job:...'-like keys.


def find_job_ids(job_id_matcher: str) -> Iterable[RqJobId]:
    """
    Iterate the RQ job IDs matching the given pattern.

    :param job_id_matcher: a Redis pattern to match the job ID part of an
        RQ job key.
    :return: an generator object to iterate the matching job IDs.
    """
    for k in find_job_keys(job_id_matcher):
        yield job_id_from_job_key(k)


def find_job_ids_in_registry(rq_reg_key: str, job_id_matcher: str) \
        -> Iterable[RqJobId]:
    """
    Iterate RQ job IDs found in the named RQ registry that match the
    given Redis expression.

    :param rq_reg_key: the name of the RQ registry to scan.
    :param job_id_matcher: a Redis pattern to match RQ job IDs.
    :return: an generator object to iterate the matching job IDs.
    """
    redis = redis_connection()
    for jid in redis.zscan_iter(name=rq_reg_key, match=job_id_matcher):
        yield jid[0].decode('utf-8')


def find_pending_job_ids(q: Queue, job_id_matcher: str) -> Iterable[RqJobId]:
    """
    Iterate RQ job IDs of pending jobs with an ID matching the given Redis
    expression. A job is pending if its ID is found in any of these RQ job
    registries: started, deferred, scheduled.

    :param q: the queue to scan.
    :param job_id_matcher: a Redis pattern to match RQ job IDs.
    :return: an generator object to iterate the matching job IDs.
    """
    started = find_job_ids_in_registry(q.started_job_registry.key,
                                       job_id_matcher)
    deferred = find_job_ids_in_registry(q.deferred_job_registry.key,
                                        job_id_matcher)
    scheduled = find_job_ids_in_registry(q.scheduled_job_registry.key,
                                         job_id_matcher)
    return chain(started, deferred, scheduled)


def find_successful_job_ids(q: Queue, job_id_matcher: str) \
        -> Iterable[RqJobId]:
    """
    Iterate RQ job IDs found in the specified queue's finished job registry
    that match the given Redis expression.

    :param q: the queue to scan.
    :param job_id_matcher: a Redis pattern to match RQ job IDs.
    :return: an generator object to iterate the matching job IDs.
    """
    return find_job_ids_in_registry(
        q.finished_job_registry.key, job_id_matcher)


def find_failed_job_ids(q: Queue, job_id_matcher: str) -> Iterable[RqJobId]:
    """
    Iterate RQ job IDs found in the specified queue's failed job registry
    that match the given Redis expression.

    :param q: the queue to scan.
    :param job_id_matcher: a Redis pattern to match RQ job IDs.
    :return: an generator object to iterate the matching job IDs.
    """
    return find_job_ids_in_registry(
        q.failed_job_registry.key, job_id_matcher)


def count_pending_jobs(q: Queue) -> int:
    """
    Count all pending jobs for the given queue.

    :param q: the target queue.
    :return: pending job tally.
    """
    queued = q.count
    deferred = q.deferred_job_registry.count
    scheduled = q.scheduled_job_registry.count
    return queued + deferred + scheduled
# NOTE. Consistency.
# This is kind of accurate but not consistent with find_pending_job_ids.
# That's the best we can do at the moment, but we should revisit it in
# the future.


def count_successful_jobs(q: Queue) -> int:
    """
    Count all successful jobs for the given queue.

    :param q: the target queue.
    :return: successful job tally.
    """
    return q.finished_job_registry.count


def count_failed_jobs(q: Queue) -> int:
    """
    Count all failed jobs for the given queue.

    :param q: the target queue.
    :return: failed job tally.
    """
    return q.failed_job_registry.count


def count_jobs(q: Queue) -> int:
    """
    Count all jobs for the given queue.

    :param q: the target queue.
    :return: job tally.
    """
    return count_pending_jobs(q) + count_successful_jobs(q) + \
        count_failed_jobs(q)


def load_jobs(job_ids: Iterable[RqJobId]) -> Iterable[Job]:
    """
    Iterate RQ jobs having an ID in the input set of ``job_ids``.
    Notice that the returned jobs may be less than the number of input job
    IDs since other processes acting on the RQ queues may delete or purge
    jobs while this fetch operation is in progress.

    :param job_ids: the RQ job IDs of the jobs to fetch.
    :return: an generator object to iterate the jobs.
    """
    redis = redis_connection()
    splitter = IterCostSplitter(cost_fn=lambda _: 1, batch_max_cost=100)  # (1)

    for jid_batch_iter in splitter.iter_batches(job_ids):
        jid_batch = list(jid_batch_iter)                                  # (2)
        jobs = Job.fetch_many(job_ids=jid_batch, connection=redis)
        for j in jobs:
            if j is not None:                                             # (3)
                yield j
# NOTE.
# 1. Algorithmic efficiency. Not optimal as it stands now but it should
# be decent enough in practice. In fact, we assume all jobs have the same
# computational cost which surely isn't true in general---e.g. an NGSI
# notification payload could hold a few K whereas another megs. Also the
# batch max cost is kinda arbitrary and based on the hope that in most
# common scenarios size(job_ids) ~ 100 * c for a small c so we only have
# to make a handful of Redis calls to fetch data---notice that fetch_many
# pipelines commands to fetch hashes. In principle we could do much better
# than this if, for each job ID, we knew the size of the corresponding Redis
# hash. There's actually ways to figure out Redis hash sizes:
#
# - https://redis.io/commands/memory-usage
# - https://stackoverflow.com/questions/16691715/
#
# Then if we had a set { (job_id, hash_size) }, we could find a partition
# where each class has a cost in bytes (=sum of hash_size) proportional to
# a set max cost and where the number of classes is within a certain range
# so we can minimise the number of calls to Redis.
#
# 2. Python d*ck typing. ``fetch_many`` will happily accept a generator
# object since it's iterable. But in actual fact, the implementation needs
# a list of job IDs b/c it scans the IDs twice. If you pass in a generator
# nothing will bomb out, but you'll get an empty list of jobs back which
# is kinda nasty b/c it could take a while to figure out the query predicate
# actually matched some of the job IDs so some of the jobs should've been
# returned. Happy Python, everybody! (I wish Haskell was more popular...)
#
# 3. Missing jobs. It can happen that since we got the list of job IDs,
# some of the jobs aren't in Redis anymore---e.g. a call to the delete
# endpoint, retention TTL expiry, etc.


def delete_jobs(job_ids: Iterable[RqJobId]):
    """
    Delete the specified RQ jobs.

    :param job_ids: the RQ job IDs of the jobs to delete.
    """
    for job in load_jobs(job_ids):
        job.delete()
# NOTE.
# 1. Algorithmic efficiency. Awful? But for now we're assuming this function
# only ever gets called with a handful of job IDs in situations where some
# manual clean up is needed. Normally, you'd let RQ take care of job life-cycle
# by setting suitable TTLs.
# 2. Queue clean up. The delete method takes care of removing the job from
# its queue and associated registries---have a look at the implementation.
