"""Deterministic HTML structure helpers for SEO analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class StructureReport:
    h1_count: int
    h2_count: int
    h3_count: int
    paragraph_count: int
    list_count: int
    table_count: int
    has_cta: bool
    headings: list[str]
    score: int
    issues: list[str]
    recommendations: list[str]


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "html.parser")


def plain_text(html: str) -> str:
    soup = parse_html(html)
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def analyze_structure(html: str) -> StructureReport:
    soup = parse_html(html)
    h1 = soup.find_all("h1")
    h2 = soup.find_all("h2")
    h3 = soup.find_all("h3")
    paragraphs = soup.find_all("p")
    lists = soup.find_all(["ul", "ol"])
    tables = soup.find_all("table")
    cta = bool(soup.select(".cta-block")) or bool(
        re.search(r"\b(cta|call to action|next step|get started|sign up)\b", plain_text(html), re.I)
    )
    issues: list[str] = []
    recommendations: list[str] = []
    score = 100
    if len(h1) != 1:
        issues.append("Expected exactly one H1")
        recommendations.append("Use a single clear H1 matching the primary topic")
        score -= 20 if len(h1) == 0 else 10
    if len(h2) < 2:
        issues.append("Few H2 sections")
        recommendations.append("Add clear H2 sections for major topics")
        score -= 15
    if len(paragraphs) < 3:
        issues.append("Thin paragraph structure")
        score -= 10
    if not cta:
        issues.append("No clear CTA detected")
        recommendations.append("Add a clear call-to-action near the end")
        score -= 10
    headings = [tag.get_text(" ", strip=True) for tag in (*h1, *h2, *h3)]
    return StructureReport(
        h1_count=len(h1),
        h2_count=len(h2),
        h3_count=len(h3),
        paragraph_count=len(paragraphs),
        list_count=len(lists),
        table_count=len(tables),
        has_cta=cta,
        headings=headings,
        score=max(0, min(100, score)),
        issues=issues,
        recommendations=recommendations,
    )
