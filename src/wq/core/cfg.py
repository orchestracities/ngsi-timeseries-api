"""
Interface to the configuration store and factory to build simple values
out of configuration items.
"""

import logging

from redis import Redis

from cache.factory import CacheEnvReader
from utils.cfgreader import EnvReader, BoolVar, IntVar, StrVar


def redis_connection() -> Redis:
    """
    :return: A pooled connection to the configured QuantumLeap Redis cache.
    """
    reader = CacheEnvReader()
    host = reader.redis_host() or 'localhost'
    port = reader.redis_port()
    return Redis(host=host, port=port)


OFFLOAD_WORK_VAR = BoolVar('WQ_OFFLOAD_WORK', False)


def offload_to_work_queue() -> bool:
    """
    Offload task execution to the work queue?

    :return: `True` to offload tasks to the work queue; `False` to execute
        them synchronously within the calling thread.
    """
    return EnvReader().safe_read(OFFLOAD_WORK_VAR)


RECOVER_FROM_ENQUEUEING_FAILURE_VAR = \
    BoolVar('WQ_RECOVER_FROM_ENQUEUEING_FAILURE', False)


def recover_from_enqueueing_failure() -> bool:
    """
    Attempt to run tasks synchronously if the queue is temporarily not
    available? When offloading task execution to the work queue, it could
    happen that the queueing of a task fails, e.g. the queue backend is
    down and the task can't be added to the work queue. In that case, if
    this function returns ``True``, then QL tries to recover from the
    error by executing the task synchronously in the calling thread.
    On the other hand, if this function returns ``False``, then QL will
    just raise an error.

    Only take this setting into account if ``offload_to_work_queue`` is
    ``True``. (If ``False``, then tasks already get run synchronously.)

    :return: ``True`` for try synchronous task execution on enqueueing
        failure, ``False`` for raise an error instead.
    """
    return EnvReader().safe_read(RECOVER_FROM_ENQUEUEING_FAILURE_VAR)


def default_queue_name() -> str:
    """
    :return: the name of the default RQ queue to use for executing tasks.
    """
    return 'default'


def queue_names() -> [str]:
    """
    :return: the name of the RQ queues to use for executing tasks.
    """
    return [default_queue_name()]
# NOTE. Multiple task queues.
# For now we're just using one queue for all tasks but going forward we could
# e.g. use a separate queue for each task type to prioritise execution.


MAX_RETRIES_VAR = IntVar('WQ_MAX_RETRIES', 0)


def max_retries() -> int:
    """
    :return: how many times a failed task should be retried.
    """
    return EnvReader().safe_read(MAX_RETRIES_VAR)


def retry_intervals() -> [int]:
    """
    Build a growing sequence of exponentially spaced out intervals at which
    to retry failed tasks. Each value is in seconds and in total there are
    `max_retries()` values.

    :return: a list of retry intervals in seconds.
    """
    base_delay = 20  # seconds
    return [(2**k) * base_delay for k in range(0, max_retries())]    # (2)
# NOTE.
# 1. Keeping it simple for now.
# But in the future, we may want to have different retry strategies and
# intervals for each task type, make the delay configurable, etc.
# 2. Exponential back-off.
# What we have here isn't exponential back-off as in e.g.
# - https://en.wikipedia.org/wiki/Exponential_backoff
# but rather exponential delay since th RQ scheduler only accepts a list of
# retry intervals.


FAILURE_TTL_VAR = IntVar('WQ_FAILURE_TTL', 60 * 60 * 24 * 7)  # a week


def failed_task_retention_period() -> int:
    """
    How long to keep failed tasks in the system. Past that period, failed
    tasks get deleted. Notice if you configure a task with retries, then
    it gets flagged as "failed" only after all retries attempts have failed.

    :return: how long, in seconds, to keep failed tasks.
    """
    return EnvReader().safe_read(FAILURE_TTL_VAR)


SUCCESS_TTL_VAR = IntVar('WQ_SUCCESS_TTL', 60 * 60 * 24)  # a day


def successful_task_retention_period() -> int:
    """
    How long to keep successfully executed tasks in the system. Past that
    period, any successful task gets deleted.

    :return: how long, in seconds, to keep successful tasks.
    """
    return EnvReader().safe_read(SUCCESS_TTL_VAR)

# NOTE. Retention periods.
# In the future we could have more fine-grained configuration so e.g. each
# task type gets different retention periods.


LOG_LEVEL_VAR = StrVar('LOGLEVEL', 'INFO')


def log_level() -> int:
    """
    Read the log level to use from the ``LOGLEVEL`` environment variable.
    If the variable isn't set, return the info level ID. If set but its
    value isn't one of the strings recognised by the ``logging`` lib
    (case-insensitive comparison), then return the info level ID again.
    Otherwise return the corresponding log level ID.

    :return: one of the log level IDs known to the ``logging`` lib.
    """
    r = EnvReader()
    level_name = r.safe_read(LOG_LEVEL_VAR).upper()
    try:
        return logging._nameToLevel[level_name]
    except KeyError:
        return logging.INFO
