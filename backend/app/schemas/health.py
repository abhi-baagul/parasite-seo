from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)
    request_id: str | None = None


class HealthComponent(BaseModel):
    status: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    database: HealthComponent
    redis: HealthComponent
