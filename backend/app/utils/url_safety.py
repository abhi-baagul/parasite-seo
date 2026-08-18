"""Safe URL validation for links and embeds (Phase 4)."""

from urllib.parse import urlparse

from app.core.config import settings
from app.core.exceptions import BadRequestError

BLOCKED_SCHEMES = {"javascript", "data", "file", "vbscript", "blob", "about"}
ALLOWED_VIDEO_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "m.youtube.com",
    "vimeo.com",
    "www.vimeo.com",
    "player.vimeo.com",
}


def validate_safe_url(url: str, *, allow_http: bool | None = None) -> str:
    value = (url or "").strip()
    if not value:
        raise BadRequestError("URL is required")
    parsed = urlparse(value)
    scheme = (parsed.scheme or "").lower()
    if scheme in BLOCKED_SCHEMES or not scheme:
        raise BadRequestError(f"Unsafe or missing URL scheme rejected: {scheme or '(none)'}")
    http_ok = settings.allow_http_links if allow_http is None else allow_http
    allowed = {"https"} | ({"http"} if http_ok else set())
    if scheme not in allowed:
        raise BadRequestError(f"Only {', '.join(sorted(allowed))} URLs are allowed")
    if not parsed.netloc:
        raise BadRequestError("URL must include a host")
    return value


def validate_video_embed_url(url: str) -> str:
    value = validate_safe_url(url)
    host = urlparse(value).netloc.lower()
    if host not in ALLOWED_VIDEO_HOSTS and not any(host.endswith(f".{h}") for h in ("youtube.com", "vimeo.com")):
        raise BadRequestError("Video embed host must be YouTube or Vimeo (or leave empty for user-owned later)")
    return value


def slugify(value: str, *, max_length: int = 80) -> str:
    import re

    text = (value or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:max_length] or "content"
