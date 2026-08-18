"""Keyword / topic coverage analysis (editorial, not ranking prediction)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.seo.structure import parse_html, plain_text


@dataclass
class KeywordAnalysisResult:
    primary_keyword: str | None
    primary_keyword_present: bool
    secondary_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    overused_terms: list[str] = field(default_factory=list)
    related_terms: list[str] = field(default_factory=list)
    placement: dict = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    score: int = 0


def _count_phrase(text: str, phrase: str) -> int:
    if not phrase:
        return 0
    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    return len(pattern.findall(text))


def analyze_keywords(
    html: str,
    *,
    title: str | None,
    primary_keyword: str | None,
    secondary_keywords: list[str] | None = None,
) -> KeywordAnalysisResult:
    text = plain_text(html)
    soup = parse_html(html)
    secondaries = [k for k in (secondary_keywords or []) if k]
    primary = primary_keyword.strip() if primary_keyword else None
    issues_rec: list[str] = []
    missing: list[str] = []
    overused: list[str] = []

    primary_count = _count_phrase(text, primary or "")
    primary_present = primary_count > 0

    h1 = soup.find("h1")
    h1_text = h1.get_text(" ", strip=True) if h1 else ""
    intro = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p")[:2])
    conclusion = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p")[-2:])
    heading_blob = " ".join(t.get_text(" ", strip=True) for t in soup.find_all(["h1", "h2", "h3"]))

    placement = {
        "in_title": bool(primary and title and primary.lower() in title.lower()),
        "in_h1": bool(primary and primary.lower() in h1_text.lower()),
        "in_introduction": bool(primary and primary.lower() in intro.lower()),
        "in_headings": bool(primary and primary.lower() in heading_blob.lower()),
        "in_conclusion": bool(primary and primary.lower() in conclusion.lower()),
        "primary_count": primary_count,
    }

    if primary and not primary_present:
        missing.append(primary)
        issues_rec.append("Primary keyword is missing from the article body")
    if primary and primary_count >= 12:
        overused.append(primary)
        issues_rec.append("Primary keyword appears excessively — reduce unnatural repetition")

    present_secondaries: list[str] = []
    for kw in secondaries:
        count = _count_phrase(text, kw)
        if count == 0:
            missing.append(kw)
        else:
            present_secondaries.append(kw)
        if count >= 8:
            overused.append(kw)

    if missing:
        issues_rec.append("Cover missing keywords naturally where they fit the topic")
    if not placement["in_h1"] and primary:
        issues_rec.append("Consider reflecting the primary keyword in the H1 when natural")

    # Soft score: presence + placement + avoid stuffing
    score = 50
    if primary_present:
        score += 20
    if placement["in_title"]:
        score += 8
    if placement["in_h1"]:
        score += 8
    if placement["in_introduction"]:
        score += 5
    covered = len(present_secondaries)
    score += min(15, covered * 4)
    score -= min(25, len(overused) * 10)
    score -= min(20, len([m for m in missing if m == primary]) * 20)

    related = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text):
        low = token.lower()
        if primary and low in primary.lower():
            continue
        if low not in related and low not in {k.lower() for k in secondaries}:
            related.append(token)
        if len(related) >= 8:
            break

    return KeywordAnalysisResult(
        primary_keyword=primary,
        primary_keyword_present=primary_present,
        secondary_keywords=present_secondaries,
        missing_keywords=missing,
        overused_terms=overused,
        related_terms=related,
        placement=placement,
        recommendations=issues_rec,
        score=max(0, min(100, score)),
    )
