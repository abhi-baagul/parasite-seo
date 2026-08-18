"""Development-only seed data. Never run against production.

Run: python -m app.db.seed
"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.core.security import hash_password
from app.models.campaign import Campaign
from app.models.content import ContentAsset, ContentLink
from app.models.enums import (
    CampaignStatus,
    ContentStatus,
    ContentType,
    LinkAttribute,
    LinkStatus,
    ProjectStatus,
    PromptStatus,
)
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.user import User
from app.repositories.user import UserRepository


def seed_development_data(session: Session) -> User:
    if settings.is_production:
        raise ForbiddenError("Development seed data cannot run in production")

    repo = UserRepository(session)
    existing = repo.get_by_email(settings.seed_user_email)
    if existing:
        return existing

    user = User(
        email=settings.seed_user_email.lower(),
        password_hash=hash_password(settings.seed_user_password),
        name="Ashish Rao",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    session.flush()

    solar = Project(
        user_id=user.id,
        name="Home Solar Buyer's Guides",
        description="Authorized comparison content for residential solar.",
        niche="Residential solar",
        country="United States",
        language="English",
        target_audience="Homeowners evaluating solar + battery",
        monetization_model="sponsored_assessment",
        status=ProjectStatus.ACTIVE.value,
    )
    payroll = Project(
        user_id=user.id,
        name="SaaS Payroll Comparisons",
        description="Guides for finance leads on authorized Workstack properties.",
        niche="HR tech",
        country="United States",
        language="English",
        target_audience="Finance and People ops leads",
        monetization_model="demo_request",
        status=ProjectStatus.ACTIVE.value,
    )
    session.add_all([solar, payroll])
    session.flush()

    solar_campaign = Campaign(
        project_id=solar.id,
        name="Q3 Hybrid Inverter Cluster",
        description="Comparison and supporting explainers.",
        status=CampaignStatus.ACTIVE.value,
        target_country="United States",
        language="English",
        default_content_type=ContentType.COMPARISON.value,
        default_word_count=1800,
    )
    payroll_campaign = Campaign(
        project_id=payroll.id,
        name="Mid-market payroll series",
        description="Implementation-focused payroll guides.",
        status=CampaignStatus.ACTIVE.value,
        target_country="United States",
        language="English",
        default_content_type=ContentType.GUIDE.value,
        default_word_count=1200,
    )
    session.add_all([solar_campaign, payroll_campaign])
    session.flush()

    solar_prompt = Prompt(
        project_id=solar.id,
        campaign_id=solar_campaign.id,
        raw_prompt="Write a 2026 comparison of hybrid solar inverters for US homeowners.",
        status=PromptStatus.USED.value,
    )
    payroll_prompt = Prompt(
        project_id=payroll.id,
        campaign_id=payroll_campaign.id,
        raw_prompt="Write a practical framework for comparing mid-market payroll platforms.",
        status=PromptStatus.ANALYZED.value,
    )
    session.add_all([solar_prompt, payroll_prompt])
    session.flush()

    solar_content = ContentAsset(
        project_id=solar.id,
        campaign_id=solar_campaign.id,
        prompt_id=solar_prompt.id,
        title="Best Hybrid Solar Inverters for Homeowners in 2026",
        slug="best-hybrid-solar-inverters-2026",
        content="<p>Hybrid inverters sit between rooftop panels, a home battery, and the grid.</p>",
        content_type=ContentType.COMPARISON.value,
        status=ContentStatus.APPROVED.value,
        word_count=1840,
        seo_score=86,
        quality_score=82,
    )
    payroll_content = ContentAsset(
        project_id=payroll.id,
        campaign_id=payroll_campaign.id,
        prompt_id=payroll_prompt.id,
        title="How Mid-Market Teams Should Compare Payroll Platforms",
        slug="compare-payroll-platforms-mid-market",
        content="<p>Most payroll RFPs overweight UI screenshots.</p>",
        content_type=ContentType.GUIDE.value,
        status=ContentStatus.GENERATED.value,
        word_count=1260,
        seo_score=71,
        quality_score=74,
    )
    session.add_all([solar_content, payroll_content])
    session.flush()

    session.add_all(
        [
            ContentLink(
                content_asset_id=solar_content.id,
                target_url="https://partners.energyreview.co/solar-assessment",
                anchor_text="Book a qualified assessment",
                placement_description="Closing CTA",
                link_attribute=LinkAttribute.SPONSORED.value,
                status=LinkStatus.INSERTED.value,
            ),
            ContentLink(
                content_asset_id=payroll_content.id,
                target_url="https://workstack.io/payroll-demo",
                anchor_text="See the payroll implementation checklist",
                placement_description="Mid-article callout",
                link_attribute=LinkAttribute.STANDARD.value,
                status=LinkStatus.PLANNED.value,
            ),
        ]
    )
    session.flush()
    return user


if __name__ == "__main__":
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        user = seed_development_data(session)
        session.commit()
        print(f"Seeded development user {user.email} ({user.id})")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
