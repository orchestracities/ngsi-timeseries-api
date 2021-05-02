from enum import Enum
from typing import Callable, Iterable, Optional

from pydantic import BaseModel
from rq.job import Job, JobStatus

from wq.task import WorkQ, _tasklet_from_rq_job
from wq.rqutils import RqJobId, find_job_ids, find_failed_job_ids, \
    find_successful_job_ids, find_pending_job_ids, load_jobs, delete_jobs, \
    starts_with_matcher


class TaskStatus(Enum):
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    UNKNOWN = 'unknown'


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
    task_id: str
    task_type: str
    status: TaskStatus
    retries_left: Optional[int]


class TaskInfo(BaseModel):
    runtime: TaskRuntimeInfo
    input: BaseModel


def _task_info_from_rq_job(j: Job) -> TaskInfo:
    tasklet = _tasklet_from_rq_job(j)
    status = _task_status_from_job_status(j.get_status())
    return TaskInfo(
        runtime=TaskRuntimeInfo(
            task_id=tasklet.task_id().id_repr(),
            task_type=str(type(tasklet)),
            status=status,
            retries_left=j.retries_left
        ),
        input=tasklet.task_input()
    )


class QMan:

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
        return QMan._load(find_job_ids, task_id_prefix)

    @staticmethod
    def delete_tasks(task_id_prefix: str):
        matcher = starts_with_matcher(task_id_prefix)
        job_ids = find_job_ids(matcher)
        delete_jobs(job_ids)

    def count_pending_tasks(self, task_id_prefix: str) -> int:
        return self._count_tasks(self._pending_jid_finder, task_id_prefix)

    def count_successful_tasks(self, task_id_prefix: str) -> int:
        return self._count_tasks(self._successful_jid_finder, task_id_prefix)

    def count_failed_tasks(self, task_id_prefix: str) -> int:
        return self._count_tasks(self._failed_jid_finder, task_id_prefix)

    def load_pending_tasks(self, task_id_prefix: str) -> Iterable[TaskInfo]:
        return self._load(self._pending_jid_finder, task_id_prefix)

    def load_successful_tasks(self, task_id_prefix: str) -> Iterable[TaskInfo]:
        return self._load(self._successful_jid_finder, task_id_prefix)

    def load_failed_tasks(self, task_id_prefix: str) -> Iterable[TaskInfo]:
        return self._load(self._failed_jid_finder, task_id_prefix)
