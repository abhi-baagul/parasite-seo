"""Thin facade for prompt analysis workflows (Phase 3)."""

from app.services.content_generation import analyze_prompt, confirm_requirements

__all__ = ["analyze_prompt", "confirm_requirements"]
