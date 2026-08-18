"""Simple readability diagnostics (editorial)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.seo.structure import plain_text


@dataclass
class ReadabilityReport:
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    score: int
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def analyze_readability(html: str, *, target_word_count: int | None = None) -> ReadabilityReport:
    text = plain_text(html)
    words = [w for w in re.findall(r"\b[\w'-]+\b", text)]
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    word_count = len(words)
    sentence_count = max(1, len(sentences))
    avg = word_count / sentence_count
    issues: list[str] = []
    recs: list[str] = []
    score = 90
    if avg > 28:
        issues.append("Average sentence length is high")
        recs.append("Shorten long sentences for readability")
        score -= 15
    if word_count < 300:
        issues.append("Content is short")
        score -= 20
    if target_word_count and word_count < int(target_word_count * 0.6):
        issues.append("Word count is below the requested range")
        recs.append("Expand sections that still need explanation")
        score -= 10
    return ReadabilityReport(
        word_count=word_count,
        sentence_count=sentence_count,
        avg_sentence_length=round(avg, 1),
        score=max(0, min(100, score)),
        issues=issues,
        recommendations=recs,
    )
