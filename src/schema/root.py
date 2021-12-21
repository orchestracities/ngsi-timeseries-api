from typing import Optional

from pydantic import BaseModel


class Version(BaseModel):
    version: str


class API(BaseModel):
    v2: str


class ErrorResponse(BaseModel):
    description: str
    error: Optional[str]
