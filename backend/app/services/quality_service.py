"""Thin facade for quality/SEO checks (Phase 3)."""

from app.services.content_generation import list_quality_checks, run_optimize, run_quality_check, run_seo_check

__all__ = ["run_seo_check", "run_quality_check", "list_quality_checks", "run_optimize"]
