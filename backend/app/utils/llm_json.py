"""Coerce common LLM JSON quirks before Pydantic validation."""

from __future__ import annotations

import json
import re
from typing import Any, get_args, get_origin

from pydantic import BaseModel


TRUE_STRINGS = {"true", "yes", "y", "1", "required", "clear cta", "cta"}
FALSE_STRINGS = {"false", "no", "n", "0", "not required", "none", "null"}


def extract_json_object(content: str | list | dict | None) -> Any | None:
    if content is None:
        return None
    if isinstance(content, (dict, list)):
        return content
    if isinstance(content, list):  # pragma: no cover - handled above
        return content
    if not isinstance(content, str):
        return None
    text = content.strip()
    if not text:
        return None
    # Strip markdown fences.
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def _unwrap_payload(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    for key in ("data", "result", "output", "requirements", "analysis"):
        inner = data.get(key)
        if isinstance(inner, dict) and len(inner) > 2:
            return inner
    return data


def _coerce_bool(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        low = value.strip().lower()
        if low in {"", "null", "none", "unknown", "n/a", "na"}:
            return None
        if low in TRUE_STRINGS or "cta" in low or "call to action" in low:
            return True
        if low in FALSE_STRINGS:
            return False
        return True
    return value


def _coerce_int(value: Any) -> Any:
    if value is None or isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        match = re.search(r"\d+", cleaned)
        if not match:
            return None
        return int(match.group(0))
    return value


def _coerce_list(value: Any) -> Any:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if "\n" in text:
            return [part.strip() for part in text.splitlines() if part.strip()]
        return [part.strip() for part in text.split(",") if part.strip()]
    return value


def _annotation_kinds(annotation: Any) -> set[str]:
    kinds: set[str] = set()
    origin = get_origin(annotation)
    args = get_args(annotation)
    candidates = [annotation, *(args or ())]
    if origin is not None:
        candidates.append(origin)
    for item in candidates:
        if item is bool:
            kinds.add("bool")
        elif item is int:
            kinds.add("int")
        elif item is list or get_origin(item) is list:
            kinds.add("list")
        elif item is str:
            kinds.add("str")
    return kinds


def coerce_for_schema(schema_model: type[BaseModel], data: Any) -> Any:
    data = _unwrap_payload(data)
    if not isinstance(data, dict):
        return data
    fields = getattr(schema_model, "model_fields", {})
    coerced = dict(data)
    for name, field in fields.items():
        if name not in coerced:
            continue
        value = coerced[name]
        kinds = _annotation_kinds(field.annotation)
        if "bool" in kinds and "list" not in kinds:
            coerced[name] = _coerce_bool(value)
        elif "int" in kinds and "list" not in kinds:
            coerced[name] = _coerce_int(value)
        elif "list" in kinds:
            coerced[name] = _coerce_list(value)
        elif value == "" and "str" in kinds:
            coerced[name] = None
    return coerced
