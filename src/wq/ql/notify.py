from typing import Callable, Iterable, List, Optional

from pydantic import BaseModel

from reporter.httputil import *
from translators.factory import translator_for, error_analyser_for
from wq.core import TaskInfo, TaskStatus, QMan, \
    CompositeTaskId, Tasklet, WorkQ, StopTask
import wq.core.cfg as cfg
from wq.ql.flaskutils import build_json_array_response_stream
import logging


def log():
    logger = logging.getLogger(__name__)
    return logger


class FiwareTaskId(CompositeTaskId):

    def __init__(self,
                 fiware_service: Optional[str],
                 fiware_service_path: Optional[str],
                 fiware_correlation_id: Optional[str]):
        super().__init__(
            fiware_service or '',
            fiware_service_path or '',
            fiware_correlation_id or ''
        )

    def fiware_tags_repr(self) -> str:
        return self.id_repr_initial_segment(3)

    def fiware_svc_and_svc_path_repr(self) -> str:
        return self.id_repr_initial_segment(2)


class InsertActionInput(BaseModel):
    fiware_service: Optional[str]
    fiware_service_path: Optional[str]
    fiware_correlator: Optional[str]
    payload: List[dict]


class InsertAction(Tasklet):

    @staticmethod
    def insert_queue() -> WorkQ:
        return InsertAction('', '', '', []).work_queue()

    def task_id(self) -> FiwareTaskId:
        return self._id

    def task_input(self) -> BaseModel:
        return self._input

    def __init__(self,
                 fiware_service: Optional[str],
                 fiware_service_path: Optional[str],
                 fiware_correlation_id: Optional[str],
                 payload: [dict],
                 retry_intervals: [int] = None):
        self._id = FiwareTaskId(fiware_service, fiware_service_path,
                                fiware_correlation_id)
        self._input = InsertActionInput(
            fiware_service=fiware_service,
            fiware_service_path=fiware_service_path,
            fiware_correlator=fiware_correlation_id,
            payload=payload
        )
        self._retry_int = retry_intervals
# NOTE. RQ arguments.
# We always invoke RQ jobs with one argument, namely the Tasklet itself.
# One reason for doing this is that RQ args is just an array, so there's
# no label associated to each argument. So we collect call arguments in
# a Tasklet object to be able to name them. This way we can always tell
# what the arguments of the method we want to call are, even if they get
# reordered in the method signature.

    def retry_intervals(self) -> [int]:
        if self._retry_int is None:
            return cfg.retry_intervals()
        return self._retry_int

    def run(self):
        data = self.task_input()
        svc = data.fiware_service
        svc_path = data.fiware_service_path
        try:
            with translator_for(svc) as trans:
                trans.insert(data.payload, svc, svc_path)
        except Exception as e:
            self._handle_exception(svc, e)

    @staticmethod
    def _handle_exception(fiware_service: str, e: Exception):
        if not cfg.offload_to_work_queue():
            raise e

        analyzer = error_analyser_for(fiware_service, e)
        if analyzer.can_retry_insert():
            raise e
        raise StopTask() from e


def build_task_id_init_segment():
    fid = FiwareTaskId(fiware_s(), fiware_sp(), fiware_correlator())
    if fiware_correlator():
        return fid.fiware_tags_repr()
    return fid.fiware_svc_and_svc_path_repr()


def has_fiware_headers() -> bool:
    hs = [fiware_s(), fiware_sp(), fiware_correlator()]
    ks = [h for h in hs if h]
    return len(ks) > 0


def insert_task_finder(task_status: Optional[str] = None) \
        -> Callable[[str], Iterable[TaskInfo]]:
    qman = QMan(InsertAction.insert_queue())
    if task_status == TaskStatus.PENDING.value:
        return qman.load_pending_tasks
    if task_status == TaskStatus.SUCCEEDED.value:
        return qman.load_successful_tasks
    if task_status == TaskStatus.FAILED.value:
        return qman.load_failed_tasks
    return qman.load_tasks


def list_insert_tasks(task_status: Optional[str] = None):
    task_id_prefix = build_task_id_init_segment()
    find_tasks = insert_task_finder(task_status)
    response_payload = find_tasks(task_id_prefix)
    log().info("Retrieved notification tasks to the work queue successfully")

    return build_json_array_response_stream(response_payload)
# TODO error handling


def list_insert_tasks_runtime_info():
    task_id_prefix = build_task_id_init_segment()
    response_payload = QMan.load_tasks_runtime_info(task_id_prefix)
    log().info("Retrieved summary of notification tasks to the work queue successfully")

    return build_json_array_response_stream(response_payload)
# TODO error handling


def delete_insert_tasks():
    qman = QMan(InsertAction.insert_queue())
    task_id_prefix = build_task_id_init_segment()
    qman.delete_tasks(task_id_prefix)
    log().info("Deleted notifcation tasks from the work queue successfully")
# TODO error handling


def insert_task_count_calculator(task_status: Optional[str] = None) \
        -> Callable[[Optional[str]], int]:
    qman = QMan(InsertAction.insert_queue())
    if task_status == TaskStatus.PENDING.value:
        return qman.count_pending_tasks
    if task_status == TaskStatus.SUCCEEDED.value:
        return qman.count_successful_tasks
    if task_status == TaskStatus.FAILED.value:
        return qman.count_failed_tasks
    return qman.count_all_tasks


def count_insert_tasks(task_status: Optional[str] = None):
    task_id_prefix = None
    if has_fiware_headers():
        task_id_prefix = build_task_id_init_segment()

    calculate = insert_task_count_calculator(task_status)
    return calculate(task_id_prefix)
