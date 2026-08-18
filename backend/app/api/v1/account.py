from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import SuccessResponse
from app.services import account as account_service

router = APIRouter(tags=["account"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    timezone: str | None = Field(default=None, max_length=80)
    organization: str | None = Field(default=None, max_length=200)
    job_title: str | None = Field(default=None, max_length=120)
    website: str | None = Field(default=None, max_length=2048)
    bio: str | None = None
    notification_prefs: dict[str, bool] | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


@router.post("/auth/login", response_model=SuccessResponse[dict])
def login(payload: LoginRequest, session: DbSession) -> SuccessResponse[dict]:
    return SuccessResponse(data=account_service.login(session, payload.email, payload.password))


@router.post("/auth/logout", response_model=SuccessResponse[dict])
def logout() -> SuccessResponse[dict]:
    return SuccessResponse(data={"signed_out": True})


@router.get("/me", response_model=SuccessResponse[dict])
def get_me(user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=account_service.serialize_user(user))


@router.patch("/me", response_model=SuccessResponse[dict])
def update_me(payload: ProfileUpdateRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=account_service.update_profile(session, user, payload.model_dump(exclude_unset=True)))


@router.post("/me/password", response_model=SuccessResponse[dict])
def change_password(payload: PasswordChangeRequest, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    account_service.change_password(session, user, payload.current_password, payload.new_password)
    return SuccessResponse(data={"updated": True})


@router.get("/me/notifications", response_model=SuccessResponse[list[dict]])
def list_notifications(session: DbSession, user: CurrentUser) -> SuccessResponse[list[dict]]:
    return SuccessResponse(data=account_service.list_notifications(session, user))


@router.post("/me/notifications/read-all", response_model=SuccessResponse[dict])
def mark_all_read(session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    count = account_service.mark_all_read(session, user)
    return SuccessResponse(data={"updated": count})


@router.post("/me/notifications/{notification_id}/read", response_model=SuccessResponse[dict])
def mark_read(notification_id: UUID, session: DbSession, user: CurrentUser) -> SuccessResponse[dict]:
    return SuccessResponse(data=account_service.mark_notification(session, user, notification_id, is_read=True))
