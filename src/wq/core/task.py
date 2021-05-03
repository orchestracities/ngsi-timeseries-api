from abc import ABC, abstractmethod
from uuid import uuid4

from pydantic import BaseModel
from rq import Queue
from rq.job import Job

from utils.b64 import to_b64_list, from_b64_list
from wq.core.cfg import redis_connection, default_queue_name, \
    offload_to_work_queue, failed_task_retention_period, \
    successful_task_retention_period


class TaskId(ABC):
    """
    Abstract representation of a task ID.
    """

    @abstractmethod
    def id_repr(self) -> str:
        """
        Build a string representation of this ID that uniquely identifies
        the task having this ID.

        :return: a string uniquely identifying a task.
        """
        pass

    def __str__(self):
        return self.id_repr()


class CompositeTaskId(TaskId):
    """
    A task ID made up by a sequence of strings.
    You build a ``CompositeTaskId`` by specifying an arbitrary list of
    tags ``t1, t2, ..., tN`` which can be empty. The ID sequence you get
    is ``t1, t2, ..., tN, u`` where ``u`` is a UUID that guarantees uniqueness
    regardless of the tags you use. If you specify no tags, you'll get a
    singleton sequence containing just ``u``.
    Two ``CompositeTaskId`` are the same just in case their sequences are
    equal.

    A ``CompositeTaskId`` has a string representation of
    ::
            b(t1):b(t2):...:b(tN):b(u)

    where ``b(x)`` is the Base64 encoding of ``x``. This is the job ID
    we use to identify RQ tasks on a queue, so the full RQ job key is
    ::
            rq:job:b(t1):b(t2):...:b(tN):b(u)

    Since the colon character isn't in any ``b(x)``, given the RQ job
    key we can reconstruct the original sequence of strings that make
    up the ``CompositeTaskId``: ``t1, t2, ..., tN, u``. By the same
    token, we can safely build Redis key patterns to match a set of
    RQ job keys since the Redis wildcard characters aren't in the
    Base64 alphabet. For example, you could append a ``'*'`` glob pattern
    to the output of the ``id_repr_initial_segment`` to build a Redis
    expression to match RQ job keys that contain the first ``j`` elements
    of a given ``CompositeTaskId`` sequence, e.g. for ``j = 2``
    ::
            rq:job:b(t1):b(t2)*
    """

    @staticmethod
    def from_id_repr(r: str) -> [str]:
        """
        Parse a ``CompositeTaskId`` string representation into the sequence
        that makes up the ``CompositeTaskId``. You'll only ever get meaningful
        results if the input was a value returned by the ``id_repr`` method.

        :param r: a value returned by the ``id_repr`` method. Must not be
            ``None``.
        :return: the ID sequence.
        """
        return from_b64_list(r)

    def __init__(self, *tags):
        self._id_seq = [str(t) for t in tags] + [uuid4().hex]

    def id_seq(self) -> [str]:
        """
        :return: read-only sequence making up this ID.
        """
        return self._id_seq

    def id_repr(self) -> str:
        """
        :return: a string representation of this ID as a colon-separated list
            of Base64 values, one in correspondence of each element in the
            ID sequence.
        """
        return to_b64_list(self._id_seq)

    def id_repr_initial_segment(self, size: int) -> str:
        """
        Build the substring of ``id_repr`` that contains the first ``size``
        elements of the ID sequence.

        :param size: how many elements to take, starting from the left of
            the sequence.
        :return: the ID representation substring.
        """
        m = max(1, size)                           # (1)
        initial_segment = self._id_seq[0:m]        # (2)
        return to_b64_list(initial_segment)
# NOTE.
# 1. Never match all RQ job keys. Our IDs have at least one element,
# the UUID part, so it makes sense to have m >= 1 in all cases. This
# way, we'll never wind up matching every job known to man.
# 2. size too big? Not a problem. If the input number is >= len(_id_seq)
# then [0:m] will take the whole list.


WorkQ = Queue


class Tasklet(ABC):
    """
    TODO
    """

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def task_id(self) -> TaskId:
        """
        Build a unique object to identify this task within the work queue.

        :return: a ``TaskId`` object to identify this task.
        """
        pass

    @abstractmethod
    def task_input(self) -> BaseModel:
        """
        Build a Pydantic model object with the data and metadata the task
        needs to execute the action.

        :return: the task's input.
        """
        pass
# NOTE. RQ arguments.
# We always invoke RQ jobs with one argument, namely the Tasklet itself.
# One reason for doing this is that RQ args is just an array, so there's
# no label associated to each argument. So we collect call arguments in
# a Tasklet object to be able to name them. This way we can always tell
# what the arguments of the method we want to call are, even if they get
# reordered in the method signature.

    def queue_name(self) -> str:
        """
        Choose a work queue where to put this task. Subclasses can override
        this method if the task at hand determines the queue. Otherwise, if
        not overridden the task gets added to the default queue.

        :return: the name of the queue where to put this task.
        """
        return default_queue_name()

    def work_queue(self) -> WorkQ:
        """
        :return: the work queue where to put this task.
        """
        return Queue(self.queue_name(), connection=redis_connection())

    def success_ttl(self) -> int:
        """
        How long, in seconds, to keep a task after it has completed
        successfully. Subclasses can override if the value depends
        on the task. Otherwise, you get the default TTL from the
        configuration store.

        :return: how long to keep a task after successful completion.
        """
        return successful_task_retention_period()

    def failure_ttl(self) -> int:
        return failed_task_retention_period()

    def enqueue(self):
        if offload_to_work_queue():
            self._do_enqueue()
        else:
            run_action(self)

# TODO modularity.
# 1. Avoid if/else cases all over the show. If things get more complicated
# than the above, split into different classes and use a factory to instantiate
# depending on offload_to_work_queue value.
# 2. Make it unit-testable. Factor out Queue i/f below to be able to test
# this class in isolation easily, e.g. using mocks or stubs.

    def _do_enqueue(self):
        q = self.work_queue()
        tid = self.task_id().id_repr()                     # (1)
        job = None
        try:
            job = q.enqueue(run_action, self,
                            job_id=tid,
                            result_ttl=self.success_ttl(),
                            failure_ttl=self.failure_ttl())
        except Exception as e:
            # TODO log error and say you'll run this task on the spot
            # TODO make last ditch attempt configurable: if no redis
            # just return a 500 w/o trying DB insert.
            print(e)
            run_action(self)

        assert (job is None or job.get_id() == tid)        # (2)
# NOTE.
# 1. RQ job keys. RQ will build a Redis key out of the job ID by prefixing
# it w/ 'rq:job:'. So we've got to use our ID here, not the full job key.
# 2. Paranoia. But if the RQ API changes and job ID != tid, then all the
# monitoring queries become inconsistent and it could be a while before
# we actually realise that since there won't be any obvious clues about it.


def _tasklet_from_rq_job(j: Job) -> Tasklet:
    """
    Extract the ``Tasklet`` object from the RQ job hosting it.

    :param j: an RQ job started to run a ``Tasklet``.
        Must not be ``None``.
    :return: the ``Tasklet`` object.
    """
    return j.args[0]    # (*)
# NOTE.
# When we enqueue the Tasklet object gets set to be the only argument
# of run_action which is why the above works.


def run_action(target: Tasklet):
    target.run()
