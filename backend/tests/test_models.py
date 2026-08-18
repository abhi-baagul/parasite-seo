from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.models.campaign import Campaign
from app.models.content import ContentAsset, ContentLink, ContentVersion
from app.models.enums import ContentType, LinkAttribute, ProjectStatus
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.user import User
from app.services.redis import ping_redis


def _user(email: str | None = None) -> User:
    return User(
        email=email or f"user-{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("correct-horse-battery"),
        name="Test User",
        is_active=True,
        is_verified=False,
    )


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("secret-value")
    assert hashed != "secret-value"
    assert verify_password("secret-value", hashed)
    assert not verify_password("other", hashed)


def test_database_select(db) -> None:
    db.execute(__import__("sqlalchemy").text("SELECT 1"))


def test_redis_ping() -> None:
    assert ping_redis()["status"] == "ok"


def test_create_user_and_projects(db) -> None:
    user = _user()
    db.add(user)
    db.flush()
    project = Project(
        user_id=user.id,
        name="Solar",
        niche="Residential solar",
        status=ProjectStatus.ACTIVE.value,
    )
    db.add(project)
    db.flush()
    db.refresh(user)
    assert len(user.projects) == 1
    assert user.projects[0].name == "Solar"


def test_user_email_unique(db) -> None:
    db.add(_user("dup@example.com"))
    db.flush()
    db.add(_user("dup@example.com"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_content_requires_title(db) -> None:
    user = _user()
    db.add(user)
    db.flush()
    project = Project(user_id=user.id, name="P")
    db.add(project)
    db.flush()
    db.add(
        ContentAsset(
            project_id=project.id,
            title=None,  # type: ignore[arg-type]
            slug="x",
            content="",
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_relationships_prompt_content_link(db) -> None:
    user = _user()
    db.add(user)
    db.flush()
    project = Project(user_id=user.id, name="Payroll")
    db.add(project)
    db.flush()
    campaign = Campaign(project_id=project.id, name="Series", default_content_type=ContentType.GUIDE.value)
    db.add(campaign)
    db.flush()
    prompt = Prompt(project_id=project.id, campaign_id=campaign.id, raw_prompt="Write a guide")
    db.add(prompt)
    db.flush()
    content = ContentAsset(
        project_id=project.id,
        campaign_id=campaign.id,
        prompt_id=prompt.id,
        title="Guide",
        slug="guide",
        content="<p>Hello</p>",
        content_type=ContentType.GUIDE.value,
        word_count=12,
    )
    db.add(content)
    db.flush()
    link = ContentLink(
        content_asset_id=content.id,
        target_url="https://example.com/offer",
        anchor_text="Authorized offer",
        placement_description="CTA",
        link_attribute=LinkAttribute.SPONSORED.value,
    )
    db.add(link)
    db.flush()
    db.refresh(content)
    db.refresh(project)
    assert content.prompt.raw_prompt.startswith("Write")
    assert content.links[0].target_url.endswith("/offer")
    assert project.content_assets[0].id == content.id
    assert campaign.content_assets[0].id == content.id


def test_cannot_delete_user_with_project(db) -> None:
    user = _user()
    db.add(user)
    db.flush()
    db.add(Project(user_id=user.id, name="Owned"))
    db.flush()
    db.delete(user)
    with pytest.raises(IntegrityError):
        db.flush()


def test_cannot_delete_content_with_version(db) -> None:
    user = _user()
    db.add(user)
    db.flush()
    project = Project(user_id=user.id, name="Hist")
    db.add(project)
    db.flush()
    content = ContentAsset(project_id=project.id, title="A", slug="a", content="v1")
    db.add(content)
    db.flush()
    db.add(
        ContentVersion(
            content_asset_id=content.id,
            version_number=1,
            content="v1",
            change_summary="initial",
            created_by=user.id,
        )
    )
    db.flush()
    db.delete(content)
    with pytest.raises(IntegrityError):
        db.flush()


def test_link_attribute_constraint(db) -> None:
    user = _user()
    db.add(user)
    db.flush()
    project = Project(user_id=user.id, name="Links")
    db.add(project)
    db.flush()
    content = ContentAsset(project_id=project.id, title="A", slug="a-link", content="body")
    db.add(content)
    db.flush()
    db.add(
        ContentLink(
            content_asset_id=content.id,
            target_url="https://example.com",
            anchor_text="x",
            link_attribute="spam",
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
