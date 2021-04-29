"""
Interface to the configuration store and factory to build simple values
out of configuration items.
"""

from redis import Redis

from cache.factory import CacheEnvReader


def redis_connection() -> Redis:
    """
    :return: A pooled connection to the configured QuantumLeap Redis cache.
    """
    reader = CacheEnvReader()
    host = reader.redis_host() or 'localhost'
    port = reader.redis_port()
    return Redis(host=host, port=port)


def offload_to_work_queue() -> bool:
    """
    Offload task execution to the work queue?

    :return: `True` to offload tasks to the work queue; `False` to execute
        them synchronously within the calling thread.
    """
    return True
    # TODO read from env


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


def max_retries() -> int:
    """
    :return: how many times a failed task should be retried.
    """
    return 3
    # TODO read from env


def retry_intervals() -> [int]:
    """
    Build a growing sequence of exponentially spaced out intervals at which
    to retry failed tasks. Each value is in seconds and in total there are
    `max_retries()` values.

    :return: a list of retry intervals in seconds.
    """
    base_delay = 20  # seconds
    return [(2**k)*base_delay for k in range(0, max_retries())]    # (2)
# NOTE.
# 1. Keeping it simple for now.
# But in the future, we may want to have different retry strategies and
# intervals for each task type, make the delay configurable, etc.
# 2. Exponential back-off.
# What we have here isn't exponential back-off as in e.g.
# - https://en.wikipedia.org/wiki/Exponential_backoff
# but rather exponential delay since th RQ scheduler only accepts a list of
# retry intervals.


def failed_task_retention_period() -> int:
    """
    How long to keep failed tasks in the system. Past that period, failed
    tasks get deleted. Notice if you configure a task with retries, then
    it gets flagged as "failed" only after all retries attempts have failed.

    :return: how long, in seconds, to keep failed tasks.
    """
    return 60 * 60 * 24 * 7    # a week
    # TODO read from env


def successful_task_retention_period() -> int:
    """
    How long to keep successfully executed tasks in the system. Past that
    period, any successful task gets deleted.

    :return: how long, in seconds, to keep successful tasks.
    """
    return 60 * 60 * 24    # a day
    # TODO read from env

# NOTE. Retention periods.
# In the future we could have more fine-grained configuration so e.g. each
# task type gets different retention periods.
