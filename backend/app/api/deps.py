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
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User


def resolve_current_user(
    session: Annotated[Session, Depends(get_db)],
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> User:
    """Return the acting user.

    Optional `X-User-Id` supports multi-user testing before JWT lands.
    Without it, the configured seed user is used (created if missing).
    """
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
