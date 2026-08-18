"""Project intelligence + campaign strategy heuristics (authorized publishing only)."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.utils.html_sanitize import sanitize_html


HYBRID_BLUEPRINT = {
    "tier1": 5,
    "tier2": 10,
    "cloud": 3,
    "pr": 1,
    "outreach": 10,
    "max_tier_depth": 2,
}

CONTENT_TYPES = ["article", "guide", "comparison", "listicle", "faq", "research"]

SECRET_KEYS = {"password", "secret", "token", "api_key", "aws_secret", "credential"}


def redact(message: str) -> str:
    cleaned = message
    for key in SECRET_KEYS:
        cleaned = re.sub(rf"({key}\s*[=:]\s*)\S+", r"\1[redacted]", cleaned, flags=re.I)
    return cleaned[:2000]


def domain_of(url: str | None) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        return (parsed.netloc or "").lower()
    except Exception:
        return ""


def classify_link_kind(source_url: str, target_url: str) -> str:
    src = domain_of(source_url)
    tgt = domain_of(target_url)
    if source_url.startswith("/p/") and (not target_url or target_url.startswith("/p/")):
        return "internal"
    if src and tgt and src == tgt:
        return "internal"
    if src.startswith("localhost") and tgt.startswith("localhost"):
        return "internal"
    return "external"


def supporting_topics(*, keyword: str, secondary: list[str], prompt: str = "") -> list[str]:
    kw = (keyword or "").strip()
    low = f"{kw} {prompt}".lower()
    topics: list[str] = []
    seen: set[str] = set()

    def add(item: str) -> None:
        key = item.strip().lower()
        if not key or key in seen or key == kw.lower():
            return
        seen.add(key)
        topics.append(item.strip()[:200])

    for item in secondary:
        add(item)

    if "laptop" in low and ("program" in low or "develop" in low or "coding" in low):
        for item in (
            "Best Laptops for Computer Science Students",
            "Best Laptops for Web Development",
            "Best Laptops for AI Development",
            "Best Budget Programming Laptops",
            "MacBook vs Windows for Developers",
            "Best Laptops for Python Programming",
            "Best Laptops for Full Stack Developers",
            "How Much RAM Does a Programmer Need?",
            "Best Processors for Programming",
            "Laptop Buying Guide for Developers",
        ):
            add(item)
    elif kw:
        add(f"{kw} for beginners")
        add(f"{kw} for students")
        add(f"{kw} comparison")
        add(f"{kw} buying guide")
        add(f"Best {kw} workflows")
        add(f"{kw} vs alternatives")
        add(f"{kw} 2026 overview")
        add(f"Practical {kw} checklist")
        add(f"{kw} for remote teams")
        add(f"How to choose {kw}")

    return topics[:16]


def recommended_anchors(keyword: str) -> list[str]:
    words = [w for w in re.split(r"\s+", (keyword or "").strip()) if w]
    if not words:
        return ["related guide"]
    lower = keyword.lower()
    variants = [lower, " ".join(words[1:]).lower() if len(words) > 1 else lower]
    if "best" in variants[0]:
        variants.append(variants[0].replace("best ", "", 1))
    if "for" in lower:
        tail = lower.split("for", 1)[-1].strip()
        if tail:
            variants.append(tail)
            variants.append(f"{tail.split()[-1]}s" if not tail.endswith("s") else tail)
    unique: list[str] = []
    for item in variants:
        item = re.sub(r"\s+", " ", item).strip()[:80]
        if item and item not in unique:
            unique.append(item)
    return unique or [lower]


def recommend_strategy(*, topic_count: int, dest_types: set[str], has_cloud: bool, existing_links: int) -> dict:
    if topic_count <= 1 and not has_cloud:
        return {
            "strategy_type": "single_asset",
            "label": "Single Asset",
            "reason": "The project currently has a single primary topic, so one authorized supporting asset is enough to start.",
            "blueprint": {"tier1": 1, "tier2": 0, "cloud": 0, "pr": 0, "outreach": 0, "max_tier_depth": 1},
        }
    if has_cloud and topic_count >= 4:
        cloud = 3 if "cloud_static" in dest_types or "aws_s3" in dest_types or "azure_blob" in dest_types else 3
        return {
            "strategy_type": "hybrid",
            "label": "Hybrid Tiered Content Network",
            "reason": (
                "The project contains multiple related subtopics that can support contextual content relationships, "
                "and authorized destinations are available for web, supporting, and optional cloud pages."
            ),
            "blueprint": {**HYBRID_BLUEPRINT, "cloud": cloud, "existing_links": existing_links},
        }
    if topic_count >= 3:
        return {
            "strategy_type": "hybrid",
            "label": "Hybrid Tiered Content Network",
            "reason": "Multiple related subtopics can support a small Tier 1 / Tier 2 authorized network without mass page creation.",
            "blueprint": dict(HYBRID_BLUEPRINT),
        }
    return {
        "strategy_type": "multi_asset",
        "label": "Multi-Asset",
        "reason": "A small set of distinct supporting articles is enough for this project size.",
        "blueprint": {"tier1": 3, "tier2": 0, "cloud": 0, "pr": 0, "outreach": 0, "max_tier_depth": 1},
    }


def size_reason(blueprint: dict) -> str:
    return (
        f"Initial size is capped: {blueprint.get('tier1', 0)} Tier 1 assets linking to the target, "
        f"{blueprint.get('tier2', 0)} Tier 2 assets supporting Tier 1, "
        f"{blueprint.get('cloud', 0)} cloud pages if an authorized cloud destination exists, "
        f"{blueprint.get('pr', 0)} research/PR template, and {blueprint.get('outreach', 0)} outreach prospects "
        "(drafts only). These are planning defaults — not thousands of pages, and not a ranking guarantee."
    )


def _count(value, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def link_groups_for(blueprint: dict, dest_types: set[str]) -> list[dict]:
    groups = []
    if _count(blueprint.get("tier1")) > 0:
        groups.append({"id": "web_content", "name": "Web Content", "tier": 1, "planned": _count(blueprint.get("tier1"))})
    if _count(blueprint.get("cloud")) > 0:
        groups.append({"id": "cloud_content", "name": "Cloud Content", "tier": 1, "planned": _count(blueprint.get("cloud"))})
    if "wordpress" in dest_types or "generic_cms" in dest_types:
        groups.append({"id": "authorized_cms", "name": "Authorized CMS", "tier": 1, "planned": 0})
    if _count(blueprint.get("pr")) > 0:
        groups.append({"id": "research", "name": "Research Asset", "tier": 1, "planned": _count(blueprint.get("pr"))})
    if _count(blueprint.get("tier2")) > 0:
        groups.append({"id": "supporting", "name": "Supporting Content", "tier": 2, "planned": _count(blueprint.get("tier2"))})
    if _count(blueprint.get("outreach")) > 0:
        groups.append({"id": "outreach", "name": "Outreach", "tier": 0, "planned": _count(blueprint.get("outreach"))})
    return groups


def heading_outline(html: str) -> dict[str, list[str]]:
    def grab(tag: str) -> list[str]:
        return [sanitize_html(m).strip() for m in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", html or "", flags=re.I | re.S)]

    return {"h1": grab("h1"), "h2": grab("h2"), "h3": grab("h3")}


def build_asset_html(
    *,
    title: str,
    topic: str,
    keyword: str,
    angle: str,
    content_type: str,
    target_url: str,
    anchor: str,
    media_html: str = "",
) -> str:
    type_intro = {
        "comparison": f"This comparison looks at {topic} from a decision-making angle rather than repeating a roundup.",
        "guide": f"This practical guide covers {topic} with checklists you can verify before buying.",
        "listicle": f"This list focuses on {topic} with distinct criteria — not a copy of the money page.",
        "faq": f"These FAQs answer common questions about {topic} for a specific audience.",
        "research": f"This research template for {topic} must be filled with verified sources before publication.",
        "article": f"This article covers {topic} as a supporting angle for readers researching {keyword}.",
    }
    intro = type_intro.get(content_type, type_intro["article"])
    body = (
        f"<h1>{title}</h1>"
        f"<p>{intro}</p>"
        f"<h2>Who this is for</h2>"
        f"<p>{angle}. Readers comparing options related to {keyword} should verify specs against official product pages.</p>"
        f"<h2>Key criteria</h2>"
        "<ul><li>Workload fit</li><li>Performance versus budget</li><li>Support and upgrade path</li></ul>"
        f"{media_html}"
        f"<h2>How this relates to {keyword}</h2>"
        f"<p>If you need a broader overview, see <a href=\"{target_url}\">{anchor}</a> and confirm details there.</p>"
        f"<h3>CTA</h3>"
        f"<p>Review the full {keyword} page, then shortlist two options that match your actual workload.</p>"
        "<p><em>Editorial note: this is not a ranking, indexing, or traffic guarantee.</em></p>"
    )
    return sanitize_html(body)


def media_snippet(media: dict, *, alt: str) -> str:
    url = media.get("url") or ""
    mtype = (media.get("media_type") or "").lower()
    if "video" in mtype:
        return f'<p><em>Video placement:</em> authorized embed only when a supported provider URL exists.</p>'
    if url:
        return f'<figure><img src="{url}" alt="{alt}" /><figcaption>{alt}</figcaption></figure>'
    return ""
