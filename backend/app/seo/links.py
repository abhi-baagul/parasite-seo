"""Link analysis against HTML and planned ContentLink rows."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.seo.structure import parse_html
from app.utils.url_safety import validate_safe_url


@dataclass
class LinkReport:
    internal_count: int
    external_count: int
    planned_target_links: int
    inserted_target_links: int
    score: int
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def analyze_links(
    html: str,
    *,
    planned_links: list[dict] | None = None,
    project_slugs: set[str] | None = None,
) -> LinkReport:
    soup = parse_html(html)
    anchors = soup.find_all("a", href=True)
    internal = 0
    external = 0
    issues: list[str] = []
    recs: list[str] = []
    for a in anchors:
        href = a.get("href", "")
        try:
            validate_safe_url(href)
        except Exception:
            issues.append(f"Unsafe or invalid href found: {href[:80]}")
            continue
        if href.startswith("/") or (project_slugs and any(s in href for s in project_slugs)):
            internal += 1
        else:
            external += 1

    planned = planned_links or []
    inserted = sum(1 for link in planned if link.get("status") == "inserted")
    score = 70
    if internal >= 1:
        score += 10
    if external >= 1:
        score += 5
    if planned:
        score += 10
    if inserted:
        score += 5
    if not planned and not anchors:
        issues.append("No links planned or present")
        recs.append("Add a target link and consider internal links to related project content")
        score -= 20
    if not internal:
        recs.append("Suggest internal links to related project articles")
        score -= 5

    return LinkReport(
        internal_count=internal,
        external_count=external,
        planned_target_links=len(planned),
        inserted_target_links=inserted,
        score=max(0, min(100, score)),
        issues=issues,
        recommendations=recs,
    )
