from pydantic import BaseModel, Extra, Field, root_validator
from typing import Optional, List
import logging

from utils.common import validate_entity


def log():
    logger = logging.getLogger(__name__)
    return logger


class V2(BaseModel):
    notify_url: str
    subscriptions_url: str
    entities_url: str
    types_url: str
    attributes_url: str


class Entity(BaseModel):
    id: str = Field(
        None,
        title='The NGSI Entity ID.'
    )
    type: str = Field(
        None,
        title='The NGSI Entity Type.'
    )

    _validate_entity = root_validator(pre=True, allow_reuse=True)(
        validate_entity
    )

    class Config:
        extra = Extra.allow


class EntityKeyValue(Entity):
    class Config:
        extra = Extra.allow


class Notification(BaseModel):
    subscriptionId: Optional[str]
    data: List[Entity]


class NotificationResponse(BaseModel):
    message: str
