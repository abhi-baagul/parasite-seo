"""Aggregate editorial Content SEO Score (not a Google ranking score)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SeoScorecard:
    overall_score: int
    structure_score: int
    keyword_score: int
    readability_score: int
    metadata_score: int
    link_score: int
    media_score: int
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    checklist: list[dict] = field(default_factory=list)


def clamp(value: int) -> int:
    return max(0, min(100, int(value)))


def score_media(*, media_count: int, with_alt: int) -> tuple[int, list[str], list[str]]:
    issues: list[str] = []
    recs: list[str] = []
    if media_count == 0:
        issues.append("No media plan or assets yet")
        recs.append("Generate a media plan for sections that benefit from visuals")
        return 55, issues, recs
    score = 70 + min(20, media_count * 5)
    if with_alt < media_count:
        issues.append("Some media items are missing alt text")
        recs.append("Add concise alt text for accessibility")
        score -= 10
    return clamp(score), issues, recs


def build_scorecard(
    *,
    structure_score: int,
    keyword_score: int,
    readability_score: int,
    metadata_score: int,
    link_score: int,
    media_score: int,
    issues: list[str],
    recommendations: list[str],
    checklist: list[dict],
) -> SeoScorecard:
    # Weighted editorial blend — diagnostic only.
    overall = round(
        structure_score * 0.2
        + keyword_score * 0.2
        + readability_score * 0.15
        + metadata_score * 0.2
        + link_score * 0.15
        + media_score * 0.1
    )
    return SeoScorecard(
        overall_score=clamp(overall),
        structure_score=clamp(structure_score),
        keyword_score=clamp(keyword_score),
        readability_score=clamp(readability_score),
        metadata_score=clamp(metadata_score),
        link_score=clamp(link_score),
        media_score=clamp(media_score),
        issues=issues,
        recommendations=recommendations
        + ["Content SEO Score is an editorial diagnostic — not a Google ranking guarantee."],
        checklist=checklist,
    )


def checklist_item(key: str, label: str, status: str, detail: str | None = None) -> dict:
    return {"key": key, "label": label, "status": status, "detail": detail}
