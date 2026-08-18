from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.backlink_campaign import BacklinkCampaign
from app.models.notification import Notification
from app.models.parasite_seo import ParasiteSEOJob
from app.models.project import Project
from app.models.public_page import PublicPage
from app.models.user import User

DEFAULT_PREFS = {
    "publishing": True,
    "generation": True,
    "campaign": True,
    "agent": True,
}


def serialize_user(user: User) -> dict:
    prefs = {**DEFAULT_PREFS, **(user.notification_prefs or {})}
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "is_verified": user.is_verified,
        "timezone": user.timezone or "Asia/Kolkata",
        "organization": user.organization or "",
        "job_title": user.job_title or "",
        "website": user.website or "",
        "bio": user.bio or "",
        "role": user.job_title or "Workspace owner",
        "notification_prefs": prefs,
    }


def serialize_notification(row: Notification) -> dict:
    return {
        "id": str(row.id),
        "kind": row.kind,
        "title": row.title,
        "body": row.body,
        "href": row.href,
        "read": row.is_read,
        "at": row.created_at.isoformat() if row.created_at else None,
        "source_key": row.source_key,
    }


def login(session: Session, email: str, password: str) -> dict:
    user = session.scalar(select(User).where(User.email == email.strip().lower()))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
        "user": serialize_user(user),
    }


def update_profile(session: Session, user: User, payload: dict) -> dict:
    email = payload.get("email")
    if email and email.strip().lower() != user.email:
        taken = session.scalar(select(User).where(User.email == email.strip().lower(), User.id != user.id))
        if taken:
            raise ConflictError("That email is already in use")
        user.email = email.strip().lower()
    for key in ("name", "timezone", "organization", "job_title", "website", "bio"):
        if key in payload and payload[key] is not None:
            setattr(user, key, payload[key].strip() if isinstance(payload[key], str) else payload[key])
    if "notification_prefs" in payload and isinstance(payload["notification_prefs"], dict):
        merged = {**DEFAULT_PREFS, **(user.notification_prefs or {}), **payload["notification_prefs"]}
        user.notification_prefs = {k: bool(merged.get(k)) for k in DEFAULT_PREFS}
    session.flush()
    return serialize_user(user)


def change_password(session: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect")
    if len(new_password) < 8:
        raise BadRequestError("New password must be at least 8 characters")
    user.password_hash = hash_password(new_password)
    session.flush()


def _upsert_notification(
    session: Session,
    user: User,
    *,
    source_key: str,
    kind: str,
    title: str,
    body: str,
    href: str | None,
) -> None:
    existing = session.scalar(
        select(Notification).where(Notification.user_id == user.id, Notification.source_key == source_key)
    )
    if existing:
        return
    session.add(
        Notification(
            user_id=user.id,
            source_key=source_key,
            kind=kind,
            title=title,
            body=body,
            href=href,
            is_read=False,
        )
    )


def refresh_notifications(session: Session, user: User) -> None:
    prefs = {**DEFAULT_PREFS, **(user.notification_prefs or {})}
    _upsert_notification(
        session,
        user,
        source_key="welcome",
        kind="info",
        title="Welcome to Parasite SEO",
        body="Your workspace notifications will appear here as generations, publishes, and campaigns update.",
        href="/settings?tab=notifications",
    )
    jobs = list(session.scalars(select(ParasiteSEOJob).where(ParasiteSEOJob.user_id == user.id).limit(40)))
    for job in jobs:
        if job.status == "failed" and prefs.get("agent"):
            _upsert_notification(
                session,
                user,
                source_key=f"job:{job.id}:failed",
                kind="error",
                title="Generation failed",
                body=job.error_message or "A Parasite SEO generation hit an error.",
                href=f"/parasite-seo/{job.id}",
            )
        elif job.is_public and prefs.get("publishing"):
            _upsert_notification(
                session,
                user,
                source_key=f"job:{job.id}:published",
                kind="success",
                title="Page published",
                body=job.public_url or "A public page is live.",
                href=f"/parasite-seo/{job.id}",
            )

    pages = list(
        session.scalars(
            select(PublicPage)
            .join(Project, PublicPage.project_id == Project.id)
            .where(Project.user_id == user.id)
            .limit(20)
        )
    )
    for page in pages:
        if page.status == "published" and prefs.get("publishing"):
            _upsert_notification(
                session,
                user,
                source_key=f"page:{page.id}:published",
                kind="success",
                title="Public page is live",
                body=page.title or "A public page was published.",
                href=f"/p/{page.slug}" if page.slug else "/parasite-seo",
            )

    campaigns = list(
        session.scalars(select(BacklinkCampaign).where(BacklinkCampaign.user_id == user.id).limit(20))
    )
    for campaign in campaigns:
        if campaign.status in {"draft", "planning"} and prefs.get("campaign"):
            _upsert_notification(
                session,
                user,
                source_key=f"campaign:{campaign.id}:action",
                kind="warning",
                title="Campaign needs attention",
                body=f"{campaign.name} is still in {campaign.status}.",
                href=f"/parasite-seo/campaigns/{campaign.id}",
            )
    session.flush()


def list_notifications(session: Session, user: User) -> list[dict]:
    refresh_notifications(session, user)
    rows = list(
        session.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(40)
        )
    )
    return [serialize_notification(row) for row in rows]


def mark_notification(session: Session, user: User, notification_id: UUID, *, is_read: bool) -> dict:
    row = session.get(Notification, notification_id)
    if not row or row.user_id != user.id:
        raise UnauthorizedError("Notification not found")
    row.is_read = is_read
    session.flush()
    return serialize_notification(row)


def mark_all_read(session: Session, user: User) -> int:
    rows = list(session.scalars(select(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))))
    for row in rows:
        row.is_read = True
    session.flush()
    return len(rows)
