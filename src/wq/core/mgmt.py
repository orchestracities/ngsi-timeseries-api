"""
Data structures and operations to manage work queues.
Notice these data structures and operations abstract away the underlying
RQ implementation so clients don't have to depend on the RQ API.
"""
from enum import Enum
from typing import Callable, Iterable, List, Optional

from pydantic import BaseModel
from rq.job import Job, JobStatus

from wq.core.task import WorkQ, _tasklet_from_rq_job, RqExcMan
from wq.core.rqutils import RqJobId, find_job_ids, find_failed_job_ids, \
    find_successful_job_ids, find_pending_job_ids, load_jobs, delete_jobs, \
    starts_with_matcher, count_jobs, count_pending_jobs, count_failed_jobs, \
    count_successful_jobs


class TaskStatus(Enum):
    """
    Enumerate the states a task can be in.
    """

    PENDING = 'pending'
    """
    A task is in the pending state from the time it gets enqueued to the
    time it gets executed for the last time, i.e. until it gets retried
    for the last time if previous runs failed.
    """
    SUCCEEDED = 'succeeded'
    """
    A task is in the succeeded state if it ran to completion successfully.
    """
    FAILED = 'failed'
    """
    A task is in the failed state if it failed permanently, i.e. there
    was an error on every configured retry.
    """
    UNKNOWN = 'unknown'
    """
    A task is in the unknown state if its actual state (pending, succeeded,
    or failed) couldn't be determined. This can happen momentarily as the
    task is moved from state to state because transitions aren't atomic.
    """


def _task_status_from_job_status(s: JobStatus) -> TaskStatus:
    if s in (JobStatus.QUEUED, JobStatus.STARTED,
             JobStatus.DEFERRED, JobStatus.SCHEDULED):
        return TaskStatus.PENDING
    if s == JobStatus.FINISHED:
        return TaskStatus.SUCCEEDED
    if s == JobStatus.FAILED:
        return TaskStatus.FAILED
    return TaskStatus.UNKNOWN


class TaskRuntimeInfo(BaseModel):
    """
    Runtime info about the task such as its work queue ID and status.
    """
    task_id: str
    task_type: str
    status: TaskStatus
    retries_left: Optional[int]
    errors: List[str] = []


class TaskInfo(BaseModel):
    """
    Aggregate of task runtime info and input, i.e. the data the task got
    as input for processing.
    """
    runtime: TaskRuntimeInfo
    input: BaseModel


def _task_info_from_rq_job(j: Job) -> TaskInfo:
    tasklet = _tasklet_from_rq_job(j)
    status = _task_status_from_job_status(j.get_status())
    errors = [repr(e) for e in RqExcMan.list_exceptions(j)]
    return TaskInfo(
        runtime=TaskRuntimeInfo(
            task_id=tasklet.task_id().id_repr(),
            task_type=str(type(tasklet)),
            status=status,
            retries_left=j.retries_left,
            errors=errors
        ),
        input=tasklet.task_input()
    )


class QMan:
    """
    Operations to manage a given work queue.
    """

    def __init__(self, q: WorkQ):
        self._q = q
        self._pending_jid_finder = lambda m: find_pending_job_ids(q, m)
        self._successful_jid_finder = lambda m: find_successful_job_ids(q, m)
        self._failed_jid_finder = lambda m: find_failed_job_ids(q, m)

    @staticmethod
    def _load(jid_finder: Callable[[str], Iterable[RqJobId]],
              task_id_prefix: str) -> Iterable[TaskInfo]:
        matcher = starts_with_matcher(task_id_prefix)
        job_ids = jid_finder(matcher)
        js = load_jobs(job_ids)
        for j in js:
            yield _task_info_from_rq_job(j)

    @staticmethod
    def _count_tasks(jid_finder: Callable[[str], Iterable[RqJobId]],
                     task_id_prefix: str) \
            -> int:
        matcher = starts_with_matcher(task_id_prefix)
        job_ids = jid_finder(matcher)
        return len(list(job_ids))

    @staticmethod
    def load_tasks(task_id_prefix: str) -> Iterable[TaskInfo]:
        """
        Load all the tasks with an ID having the same prefix as the input.
        Stream data, i.e. don't load all tasks in memory but fetch them on
        demand as the consumer iterates the result set.

        :param task_id_prefix: the task ID prefix to match.
        :return: a generator to iterate the matching tasks.
        """
        return QMan._load(find_job_ids, task_id_prefix)

    @staticmethod
    def load_tasks_runtime_info(task_id_prefix: str) \
            -> Iterable[TaskRuntimeInfo]:
        """
        Same as ``load_tasks`` but only return task runtime info without
        inputs.
        """
        for t in QMan.load_tasks(task_id_prefix):
            yield t.runtime

    @staticmethod
    def delete_tasks(task_id_prefix: str):
        """
        Delete all the tasks with an ID having the same prefix as the input.

        :param task_id_prefix: the task ID prefix to match.
        """
        matcher = starts_with_matcher(task_id_prefix)
        job_ids = find_job_ids(matcher)
        delete_jobs(job_ids)

    def count_all_tasks(self, task_id_prefix: Optional[str]) -> int:
        """
        Count all the tasks with an ID having the same prefix as the input
        if given, otherwise return the total number of tasks linked to the
        work queue.

        :param task_id_prefix: the task ID prefix to match.
        :return: the number of matching tasks.
        """
        if task_id_prefix is None:
            return count_jobs(self._q)
        return self._count_tasks(find_job_ids, task_id_prefix)

    def count_pending_tasks(self, task_id_prefix: Optional[str]) -> int:
        """
        Count all the pending tasks with an ID having the same prefix as
        the input if given, otherwise return the total number of tasks
        linked to the work queue that are in the pending state.

        :param task_id_prefix: the task ID prefix to match.
        :return: the number of matching tasks.
        """
        if task_id_prefix is None:
            return count_pending_jobs(self._q)
        return self._count_tasks(self._pending_jid_finder, task_id_prefix)

    def count_successful_tasks(self, task_id_prefix: Optional[str]) -> int:
        """
        Count all the tasks with an ID having the same prefix as the input
        that executed successfully, i.e. tasks in the succeeded state. If
        the input is ``None``, count all tasks in the succeeded state that
        are linked to the queue.

        :param task_id_prefix: the task ID prefix to match.
        :return: the number of matching tasks.
        """
        if task_id_prefix is None:
            return count_successful_jobs(self._q)
        return self._count_tasks(self._successful_jid_finder, task_id_prefix)

    def count_failed_tasks(self, task_id_prefix: Optional[str]) -> int:
        """
        Count all the failed tasks with an ID having the same prefix as
        the input if given, otherwise return the total number of tasks
        linked to the work queue that are in the failed state.

        :param task_id_prefix: the task ID prefix to match.
        :return: the number of matching tasks.
        """
        if task_id_prefix is None:
            return count_failed_jobs(self._q)
        return self._count_tasks(self._failed_jid_finder, task_id_prefix)

    def load_pending_tasks(self, task_id_prefix: str) -> Iterable[TaskInfo]:
        """
        Load all the pending tasks with an ID having the same prefix as
        the input.
        Stream data, i.e. don't load all tasks in memory but fetch them on
        demand as the consumer iterates the result set.

        :param task_id_prefix: the task ID prefix to match.
        :return: a generator to iterate the matching tasks.
        """
        return self._load(self._pending_jid_finder, task_id_prefix)

    def load_successful_tasks(self, task_id_prefix: str) -> Iterable[TaskInfo]:
        """
        Load all the tasks with an ID having the same prefix as the input
        that executed successfully, i.e. tasks in the succeeded state.
        Stream data, i.e. don't load all tasks in memory but fetch them on
        demand as the consumer iterates the result set.

        :param task_id_prefix: the task ID prefix to match.
        :return: a generator to iterate the matching tasks.
        """
        return self._load(self._successful_jid_finder, task_id_prefix)

    def load_failed_tasks(self, task_id_prefix: str) -> Iterable[TaskInfo]:
        """
        Load all the failed tasks with an ID having the same prefix as
        the input.
        Stream data, i.e. don't load all tasks in memory but fetch them on
        demand as the consumer iterates the result set.

        :param task_id_prefix: the task ID prefix to match.
        :return: a generator to iterate the matching tasks.
        """
        return self._load(self._failed_jid_finder, task_id_prefix)
