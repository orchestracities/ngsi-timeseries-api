from typing import Optional

from fastapi import Header, status, Response, APIRouter
from schema.v2.v2 import V2, Notification
from reporter import api

router = APIRouter(prefix="/v2",
                   tags=["v2"],)


@router.get("/", response_model=V2)
async def v2():
    return api.list_of_api()


@router.post("/notify", response_class=Response,
          status_code=status.HTTP_201_CREATED,
          summary="Notify QuantumLeap the arrival of a new NGSI notification.")
#async when we move to sqlalchemy with async
def notify(
        response: Response,
        notification: Notification,
        fiware_Service: Optional[str] = Header(None),
        fiware_ServicePath: Optional[str] = Header(None),
        Fiware_TimeIndex_Attribute: Optional[str] = Header(None),
        Fiware_Correlator: Optional[str] = Header(None)):
    response.status_code = status.HTTP_201_CREATED
    return response
