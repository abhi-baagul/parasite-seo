"""Auth-ready dependencies.

Phase 2B uses a development principal so ownership filtering works.
Phase 3 will replace resolve_current_user with JWT validation.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token, hash_password
from app.db.session import get_db
from app.models.user import User


def resolve_current_user(
    session: Annotated[Session, Depends(get_db)],
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Return the acting user.

    Optional Bearer JWT or `X-User-Id` selects a user. Without either, the seed user is used.
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_token(token, expected_type="access")
        try:
            user_id = UUID(str(payload.get("sub")))
        except (ValueError, TypeError) as exc:
            raise UnauthorizedError("Invalid access token") from exc
        user = session.get(User, user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return user

    if x_user_id:
        try:
            user_id = UUID(x_user_id)
        except ValueError as exc:
            raise UnauthorizedError("Invalid X-User-Id header") from exc
        user = session.get(User, user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return user

    email = settings.seed_user_email.lower()
    user = session.scalar(select(User).where(User.email == email))
    if user:
        return user

    user = User(
        email=email,
        password_hash=hash_password(settings.seed_user_password),
        name="Ashish Rao",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    session.flush()
    return user


CurrentUser = Annotated[User, Depends(resolve_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
