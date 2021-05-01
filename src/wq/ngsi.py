from typing import Optional

from translators.factory import translator_for
from wq.task import Tasklet, CompositeTaskId


class FiwareTaskId(CompositeTaskId):

    def __init__(self,
                 fiware_service: Optional[str],
                 fiware_service_path: Optional[str],
                 fiware_correlator: Optional[str]):
        super().__init__(
            fiware_service or '',
            fiware_service_path or '',
            fiware_correlator or ''
        )

    def fiware_tags_repr(self) -> str:
        return self.id_repr_initial_segment(3)

    def fiware_svc_and_svc_path_repr(self) -> str:
        return self.id_repr_initial_segment(2)


class InsertAction(Tasklet):

    def task_id(self) -> FiwareTaskId:
        return self._id

    def __init__(self,
                 fiware_service: Optional[str],
                 fiware_service_path: Optional[str],
                 fiware_correlator: Optional[str],
                 payload: [dict]):
        self.fiware_service = fiware_service
        self.fiware_service_path = fiware_service_path
        self.fiware_correlator = fiware_correlator
        self.payload = payload
        self._id = FiwareTaskId(fiware_service, fiware_service_path,
                                fiware_correlator)
# NOTE. RQ arguments.
# We always invoke RQ jobs with one argument, namely the Tasklet itself.
# One reason for doing this is that RQ args is just an array, so there's
# no label associated to each argument. So we collect call arguments in
# a Tasklet object to be able to name them. This way we can always tell
# what the arguments of the method we want to call are, even if they get
# reordered in the method signature.

    def run(self):
        with translator_for(self.fiware_service) as trans:
            trans.insert(self.payload, self.fiware_service,
                         self.fiware_service_path)
        # TODO error handling & scheduled retries w/ back-off strategy

