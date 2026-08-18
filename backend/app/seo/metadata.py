"""Metadata completeness analysis."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.utils.url_safety import slugify


@dataclass
class MetadataReport:
    seo_title: str | None
    meta_description: str | None
    slug: str | None
    seo_title_length: int
    meta_description_length: int
    score: int
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def analyze_metadata(
    *,
    seo_title: str | None,
    meta_description: str | None,
    slug: str | None,
    primary_keyword: str | None = None,
) -> MetadataReport:
    issues: list[str] = []
    recs: list[str] = []
    score = 100
    title = (seo_title or "").strip()
    desc = (meta_description or "").strip()
    slug_val = (slug or "").strip()

    if not title:
        issues.append("Missing SEO title")
        recs.append("Generate or write an SEO title")
        score -= 30
    elif len(title) > 70:
        issues.append("SEO title may be too long")
        recs.append("Aim for roughly 50–60 characters when possible")
        score -= 8
    elif len(title) < 20:
        issues.append("SEO title is very short")
        score -= 8

    if not desc:
        issues.append("Missing meta description")
        recs.append("Generate a meta description with a clear benefit")
        score -= 30
    elif len(desc) > 160:
        issues.append("Meta description may be truncated in SERPs")
        score -= 8
    elif len(desc) < 70:
        issues.append("Meta description is short")
        score -= 5

    if not slug_val:
        issues.append("Missing slug")
        score -= 20
    elif slug_val != slugify(slug_val):
        issues.append("Slug is not clean/hyphenated lowercase")
        recs.append("Use a lowercase hyphen-separated slug")
        score -= 10

    if primary_keyword and title and primary_keyword.lower() not in title.lower():
        recs.append("Consider including the primary keyword in the SEO title naturally")
        score -= 5

    return MetadataReport(
        seo_title=title or None,
        meta_description=desc or None,
        slug=slug_val or None,
        seo_title_length=len(title),
        meta_description_length=len(desc),
        score=max(0, min(100, score)),
        issues=issues,
        recommendations=recs,
    )


def generate_slug_from_keyword(primary_keyword: str | None, title: str | None) -> str:
    return slugify(primary_keyword or title or "content")
