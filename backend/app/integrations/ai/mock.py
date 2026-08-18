"""Deterministic provider for tests and offline development."""

import json
from typing import Any

from app.integrations.ai.base import AICompletionResult, AIMessage, AIProvider


class MockAIProvider(AIProvider):
    name = "mock"

    def __init__(self, responses: dict[str, dict[str, Any]] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[list[AIMessage]] = []

    def complete(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format_json: bool = True,
    ) -> AICompletionResult:
        self.calls.append(messages)
        joined = " ".join(m.content for m in messages).lower()
        payload = self._pick(joined)
        text = json.dumps(payload)
        return AICompletionResult(
            content=text,
            model=model or "mock/model",
            input_tokens=max(1, len(joined) // 4),
            output_tokens=max(1, len(text) // 4),
            total_tokens=max(2, (len(joined) + len(text)) // 4),
        )

    def _pick(self, joined: str) -> dict[str, Any]:
        for key, value in self.responses.items():
            if key in joined:
                return value
        if "action:" in joined and "selected html" in joined:
            return {
                "html": "<p>Improved editorial copy for the selected section.</p>",
                "notes": "Mock section edit",
            }
        # Prefer generation before strategy/outline phrases that may appear in nested JSON.
        if "generate the article" in joined:
            return self._article()
        if "prompt analyzer" in joined or "extract structured" in joined:
            return {
                "topic": "DIClock Referral Code",
                "main_keyword": "DIClock Referral Code",
                "secondary_keywords": [
                    "DIClock Referral Code For New User",
                    "DIClock Referral Code 2026",
                    "DIClock Referral Code Latest",
                    "DIClock Referral Code Signup",
                ],
                "word_count": 1000,
                "content_type": "informational_article",
                "intent": "informational",
                "tone": "professional",
                "audience": None,
                "country": None,
                "language": "English",
                "required_headings": ["H1", "H2", "H3"],
                "required_elements": ["H1", "H2", "H3", "bullets", "table", "CTA"],
                "cta_requirement": True,
                "offer_information": 'DIClock Referral Code "WL1Z375N" - Get 40% Off on Annual Plan',
                "promotional_information": "40% Off on Annual Plan",
                "target_url_if_present": None,
                "anchor_text_if_present": None,
                "media_requirements": [],
                "special_instructions": None,
                "uncertain_fields": ["audience", "country"],
            }
        if "research brief" in joined:
            return {
                "topic_summary": "Referral codes for DIClock appear in promotional copy and should be verified against official sources.",
                "key_facts": [],
                "entities": ["DIClock", "WL1Z375N"],
                "questions": ["Is the code still valid?", "What plan does the discount apply to?"],
                "subtopics": ["What is a referral code", "How to redeem", "Eligibility", "FAQ"],
                "supporting_information": [],
                "sources": [],
                "claims_requiring_verification": [
                    "40% off annual plan claim",
                    "Referral code WL1Z375N validity",
                ],
            }
        if "content strategy" in joined:
            return {
                "content_angle": "Explain how a DIClock referral code works and how readers can verify offers.",
                "search_intent": "informational",
                "target_audience": "Prospective DIClock users evaluating signup promotions",
                "content_goals": ["Clarify referral mechanics", "Set verification expectations", "Guide next steps"],
                "recommended_structure": ["Intro", "What it is", "How it works", "Redeem", "Benefits", "FAQ", "CTA"],
                "key_topics": ["Referral code basics", "New user eligibility", "2026 offer wording"],
                "differentiation_opportunities": ["Emphasize verification over hype"],
                "cta_strategy": "Ask readers to confirm the code on the official DIClock checkout before paying.",
                "internal_link_opportunities": [],
                "external_reference_opportunities": ["Official DIClock pricing or help pages when available"],
                "media_opportunities": ["Screenshot placeholder of redemption flow"],
            }
        if "content outline" in joined or "produce an outline" in joined:
            return {
                "h1": "DIClock Referral Code: How It Works and How to Use It",
                "sections": [
                    {"heading": "Introduction", "level": 2, "purpose": "introduction", "notes": None},
                    {"heading": "What Is a DIClock Referral Code?", "level": 2, "purpose": "main", "notes": None},
                    {"heading": "How the Referral Code Works", "level": 2, "purpose": "main", "notes": None},
                    {"heading": "Referral Code for New Users", "level": 3, "purpose": "main", "notes": None},
                    {"heading": "Referral Code 2026", "level": 3, "purpose": "main", "notes": None},
                    {"heading": "How to Redeem the Code", "level": 2, "purpose": "list", "notes": "Use bullets"},
                    {"heading": "Benefits", "level": 2, "purpose": "table", "notes": "Include comparison table"},
                    {"heading": "FAQ", "level": 2, "purpose": "faq", "notes": None},
                    {"heading": "Conclusion", "level": 2, "purpose": "conclusion", "notes": None},
                    {"heading": "Next Step", "level": 2, "purpose": "cta", "notes": "Clear CTA"},
                ],
            }
        if "seo metadata options" in joined or "generate seo metadata" in joined:
            return {
                "title_options": [
                    {
                        "title": "DIClock Referral Code 2026 — Verify Before You Buy",
                        "character_count": 52,
                        "keyword_position": "start",
                        "clarity_score": 88,
                        "intent_match": 90,
                    },
                    {
                        "title": "DIClock Referral Code: How to Use It Safely",
                        "character_count": 45,
                        "keyword_position": "start",
                        "clarity_score": 86,
                        "intent_match": 85,
                    },
                    {
                        "title": "Latest DIClock Referral Code for New Users",
                        "character_count": 43,
                        "keyword_position": "middle",
                        "clarity_score": 84,
                        "intent_match": 82,
                    },
                ],
                "meta_options": [
                    {
                        "meta_description": "Learn how DIClock referral codes work, what to verify at checkout, and how to redeem offers without relying on unverified claims.",
                        "character_count": 132,
                        "primary_keyword_present": True,
                        "cta_presence": True,
                    },
                    {
                        "meta_description": "A practical guide to DIClock Referral Code offers for new users — confirm discounts on the official page before paying.",
                        "character_count": 121,
                        "primary_keyword_present": True,
                        "cta_presence": True,
                    },
                ],
                "slug": "diclock-referral-code",
                "og_title": "DIClock Referral Code Guide",
                "og_description": "Verify referral offers before checkout.",
                "twitter_title": "DIClock Referral Code Guide",
                "twitter_description": "Verify referral offers before checkout.",
            }
        if "generate tags and categories" in joined:
            return {
                "tags": ["DIClock", "Referral Code", "Productivity", "Time Tracking", "Software", "Discounts"],
                "categories": ["Software", "Productivity", "Deals"],
            }
        if "create a media plan" in joined:
            return {
                "items": [
                    {
                        "media_type": "image",
                        "placement": "After introduction",
                        "purpose": "featured",
                        "description": "Clean productivity software illustration",
                        "generation_prompt": "Create a clean professional productivity software illustration showing time tracking, calendar scheduling, and team analytics without branding logos.",
                        "alt_text": "Time tracking dashboard showing weekly productivity statistics",
                        "caption": None,
                        "suggested_filename": "diclock-referral-overview.png",
                    },
                    {
                        "media_type": "diagram",
                        "placement": "How to Redeem section",
                        "purpose": "instructional",
                        "description": "Simple redemption flow diagram",
                        "generation_prompt": "Simple three-step diagram: open checkout, enter referral code, confirm discount.",
                        "alt_text": "Three-step diagram for redeeming a referral code",
                        "caption": "Confirm the discount appears before payment.",
                        "suggested_filename": "referral-redeem-steps.png",
                    },
                ],
                "video_suggestions": [
                    {
                        "media_type": "video",
                        "placement": "After setup / redeem section",
                        "purpose": "walkthrough",
                        "description": "How to redeem a referral code at checkout",
                        "generation_prompt": None,
                        "alt_text": None,
                        "caption": "Authorized walkthrough video if available",
                        "suggested_filename": None,
                    }
                ],
            }
        if "campaign strategy" in joined or "recommend a campaign strategy" in joined:
            return {
                "strategy_type": "hybrid",
                "label": "Hybrid Tiered Content Network",
                "reason": "The project contains multiple related subtopics that can support contextual content relationships.",
                "blueprint": {"tier1": 5, "tier2": 10, "cloud": 3, "pr": 1, "outreach": 10, "max_tier_depth": 2},
            }
        if "project intelligence" in joined or "authorized backlink campaign" in joined:
            return {
                "topic": "Best Laptops for Programming",
                "primary_keyword": "Best Laptops for Programming",
                "secondary_keywords": [
                    "Best Laptop for Developers",
                    "Best Laptop for Coding",
                    "Best Laptop for Software Development",
                    "Best Laptop for Computer Science Students",
                ],
                "search_intent": "commercial",
                "content_category": "buying_guide",
                "audience": "developers and computer science students",
                "recommended_anchor_terms": [
                    "best programming laptops",
                    "laptops for programming",
                    "programming laptops",
                    "developer laptops",
                    "laptops for software development",
                ],
                "supporting_topics": [
                    "Best Laptops for Computer Science Students",
                    "Best Laptops for Web Development",
                    "Best Laptops for AI Development",
                    "Best Budget Programming Laptops",
                    "MacBook vs Windows for Developers",
                ],
                "recommended_content_types": ["article", "comparison", "guide", "listicle"],
                "campaign_strategy": "hybrid",
                "entities": ["laptop", "developer", "programming"],
                "country": "Global",
                "language": "English",
            }
        if "link intelligence" in joined or "recommend internal links" in joined:
            return {
                "suggestions": [
                    {
                        "source_title": "Best AI Productivity Tools",
                        "target_title": "AI Tools for Students",
                        "anchor_text": "AI tools for students",
                        "placement": "After paragraph covering student use cases",
                        "context": "students are increasingly using AI",
                        "reason": "The target page provides a focused guide for student workflows.",
                        "relevance_score": 90,
                        "confidence_score": 88,
                    }
                ],
                "notes": None,
            }
        if "seo analysis" in joined:
            return {
                "overall_score": 78,
                "structure_score": 85,
                "keyword_coverage_score": 72,
                "readability_score": 80,
                "intent_score": 76,
                "issues": ["Secondary keywords could appear in one more H3"],
                "recommendations": [
                    "Keep promotional claims clearly labeled as requiring verification",
                    "This score is editorial, not a ranking guarantee",
                ],
            }
        if "quality review" in joined:
            return {
                "score": 82,
                "status": "needs_review",
                "issues": ["Offer details should be verified before publishing"],
                "recommendations": ["Add a verification note near the CTA"],
            }
        if "optimize the article" in joined:
            return {
                "suggestions": [
                    {
                        "before": "Get 40% Off on Annual Plan",
                        "after": "Promotional copy mentions up to 40% off an annual plan — confirm on the official checkout.",
                        "reason": "Reduce unsupported promotional certainty",
                    }
                ]
            }
        return self._article()

    def _article(self) -> dict[str, Any]:
        return {
            "title": "DIClock Referral Code: How It Works and How to Use It",
            "seo_title": "DIClock Referral Code Guide (Verify Before You Buy)",
            "meta_description": "Learn how DIClock referral codes work, what to verify, and how to redeem an offer without relying on unverified claims.",
            "slug": "diclock-referral-code-guide",
            "h1": "DIClock Referral Code: How It Works and How to Use It",
            "html": (
                "<h1>DIClock Referral Code: How It Works and How to Use It</h1>"
                "<h2>Introduction</h2>"
                "<p>Referral codes can reduce signup cost, but details change. Treat promotional wording as something to verify.</p>"
                "<h2>What Is a DIClock Referral Code?</h2>"
                "<p>A referral code is a promotional identifier entered during signup or checkout.</p>"
                "<h2>How the Referral Code Works</h2>"
                "<h3>Referral Code for New Users</h3>"
                "<p>New-user offers often apply only on first purchase or first subscription.</p>"
                "<h3>Referral Code 2026</h3>"
                "<p>Year-labeled offers should be checked against the current checkout terms.</p>"
                "<h2>How to Redeem the Code</h2>"
                "<ul><li>Open the official DIClock signup or checkout page.</li>"
                "<li>Enter the code exactly as provided.</li>"
                "<li>Confirm the discount appears before payment.</li></ul>"
                "<h2>Benefits</h2>"
                "<table><thead><tr><th>Item</th><th>What to verify</th></tr></thead>"
                "<tbody><tr><td>Discount amount</td><td>Shown at checkout</td></tr>"
                "<tr><td>Plan eligibility</td><td>Annual vs monthly</td></tr></tbody></table>"
                "<h2>FAQ</h2>"
                "<p><strong>Is WL1Z375N guaranteed?</strong> No. Confirm it on the official page.</p>"
                "<h2>Conclusion</h2>"
                "<p>Use referral codes carefully and verify every claim before purchasing.</p>"
                "<div class=\"cta-block\"><strong>Next step:</strong> Confirm the offer on the official DIClock checkout before you pay.</div>"
                "<p><em>Media placeholder:</em> redemption flow screenshot</p>"
            ),
            "word_count": 240,
        }
