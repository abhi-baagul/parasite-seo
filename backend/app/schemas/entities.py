from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserRead(ORMModel):
    id: UUID
    email: EmailStr
    name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class ProjectRead(ORMModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    niche: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ContentLinkRead(ORMModel):
    id: UUID
    content_asset_id: UUID
    target_url: str
    anchor_text: str
    link_attribute: str
    status: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=200)
