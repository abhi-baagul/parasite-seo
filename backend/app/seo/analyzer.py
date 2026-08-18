"""High-level SEO analyzer orchestrating modular reports."""

from __future__ import annotations

from app.seo.keywords import analyze_keywords
from app.seo.links import analyze_links
from app.seo.metadata import analyze_metadata
from app.seo.readability import analyze_readability
from app.seo.scoring import build_scorecard, checklist_item, score_media
from app.seo.structure import analyze_structure


def run_full_seo_analysis(
    *,
    html: str,
    title: str | None,
    seo_title: str | None,
    meta_description: str | None,
    slug: str | None,
    primary_keyword: str | None,
    secondary_keywords: list[str] | None,
    target_word_count: int | None,
    planned_links: list[dict] | None,
    media_count: int = 0,
    media_with_alt: int = 0,
) -> dict:
    structure = analyze_structure(html)
    keywords = analyze_keywords(
        html,
        title=seo_title or title,
        primary_keyword=primary_keyword,
        secondary_keywords=secondary_keywords,
    )
    metadata = analyze_metadata(
        seo_title=seo_title or title,
        meta_description=meta_description,
        slug=slug,
        primary_keyword=primary_keyword,
    )
    readability = analyze_readability(html, target_word_count=target_word_count)
    links = analyze_links(html, planned_links=planned_links)
    media_score, media_issues, media_recs = score_media(media_count=media_count, with_alt=media_with_alt)

    issues = (
        structure.issues
        + keywords.recommendations[:3]
        + metadata.issues
        + readability.issues
        + links.issues
        + media_issues
    )
    recommendations = (
        structure.recommendations
        + keywords.recommendations
        + metadata.recommendations
        + readability.recommendations
        + links.recommendations
        + media_recs
    )

    checklist = [
        checklist_item("title", "Title", "PASS" if (seo_title or title) else "FAIL"),
        checklist_item(
            "meta_description",
            "Meta Description",
            "PASS" if meta_description else "FAIL",
        ),
        checklist_item("slug", "Slug", "PASS" if slug else "FAIL"),
        checklist_item("h1", "H1", "PASS" if structure.h1_count == 1 else "FAIL"),
        checklist_item(
            "headings",
            "Heading Structure",
            "PASS" if structure.h2_count >= 2 else "WARNING",
        ),
        checklist_item(
            "primary_keyword",
            "Primary Keyword",
            "PASS" if keywords.primary_keyword_present else "FAIL",
        ),
        checklist_item(
            "secondary_keywords",
            "Secondary Keywords",
            "PASS" if not keywords.missing_keywords else "WARNING",
        ),
        checklist_item("cta", "CTA", "PASS" if structure.has_cta else "WARNING"),
        checklist_item(
            "internal_links",
            "Internal Links",
            "PASS" if links.internal_count else "WARNING",
        ),
        checklist_item(
            "target_link",
            "Target Link",
            "PASS" if links.planned_target_links else "WARNING",
        ),
        checklist_item("images", "Images / Media", "PASS" if media_count else "WARNING"),
        checklist_item(
            "alt_text",
            "Image Alt Text",
            "PASS" if media_count and media_with_alt >= media_count else ("WARNING" if media_count else "WARNING"),
        ),
        checklist_item(
            "readability",
            "Readability",
            "PASS" if readability.score >= 70 else "WARNING",
        ),
        checklist_item(
            "completeness",
            "Content Completeness",
            "PASS" if structure.paragraph_count >= 3 else "WARNING",
        ),
    ]

    scorecard = build_scorecard(
        structure_score=structure.score,
        keyword_score=keywords.score,
        readability_score=readability.score,
        metadata_score=metadata.score,
        link_score=links.score,
        media_score=media_score,
        issues=issues,
        recommendations=recommendations,
        checklist=checklist,
    )

    return {
        "label": "Content SEO Score",
        "disclaimer": "Editorial diagnostic only. Not a Google ranking score or guarantee.",
        "overall_score": scorecard.overall_score,
        "structure_score": scorecard.structure_score,
        "keyword_score": scorecard.keyword_score,
        "readability_score": scorecard.readability_score,
        "metadata_score": scorecard.metadata_score,
        "link_score": scorecard.link_score,
        "media_score": scorecard.media_score,
        "issues": scorecard.issues,
        "recommendations": scorecard.recommendations,
        "checklist": scorecard.checklist,
        "structure": structure.__dict__,
        "keywords": keywords.__dict__,
        "metadata": metadata.__dict__,
        "readability": readability.__dict__,
        "links": links.__dict__,
    }
