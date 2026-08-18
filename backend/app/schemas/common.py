from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class ListResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    pagination: PaginationMeta


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
