"""Publishing provider abstraction for authorized destinations (Phase 8)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from app.core.config import settings
from app.storage import LocalStorageProvider, get_storage_provider, safe_filename
from app.utils.html_sanitize import sanitize_html


@dataclass
class PublishResult:
    success: bool
    source_url: str | None
    external_id: str | None = None
    error: str | None = None
    html_snapshot: str | None = None


class PublishingProvider(ABC):
    provider_type: str

    @abstractmethod
    def test(self, configuration: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def publish(
        self,
        *,
        configuration: dict,
        title: str,
        html: str,
        slug: str,
        target_url: str,
        anchor_text: str,
        link_attribute: str = "standard",
    ) -> PublishResult:
        raise NotImplementedError

    @abstractmethod
    def unpublish(self, *, configuration: dict, external_id: str | None, source_url: str | None) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_status(self, *, configuration: dict, source_url: str | None) -> dict:
        raise NotImplementedError

    def connect(self, configuration: dict) -> dict:
        return self.test(configuration)

    def validate(self, configuration: dict) -> dict:
        return self.test(configuration)

    def update(
        self,
        *,
        configuration: dict,
        title: str,
        html: str,
        slug: str,
        target_url: str,
        anchor_text: str,
        link_attribute: str = "standard",
    ) -> PublishResult:
        return self.publish(
            configuration=configuration,
            title=title,
            html=html,
            slug=slug,
            target_url=target_url,
            anchor_text=anchor_text,
            link_attribute=link_attribute,
        )


def _inject_target_link(html: str, *, target_url: str, anchor_text: str, attribute: str) -> str:
    rel_bits = []
    if attribute == "nofollow":
        rel_bits.append("nofollow")
    if attribute == "sponsored":
        rel_bits.append("sponsored")
    if attribute == "ugc":
        rel_bits.append("ugc")
    rel = f' rel="{" ".join(rel_bits)}"' if rel_bits else ""
    link = f'<a href="{target_url}"{rel}>{anchor_text}</a>'
    body = sanitize_html(html or "")
    if anchor_text and anchor_text in body and f'href="{target_url}"' not in body:
        body = body.replace(anchor_text, link, 1)
    elif f'href="{target_url}"' not in body:
        body = body + f"<p>Related reading: {link}</p>"
    return body


class MockLocalPublishingProvider(PublishingProvider):
    """Authorized local/mock destination for development — not a third-party site."""

    provider_type = "mock_local"

    def test(self, configuration: dict) -> dict:
        return {"ok": True, "provider": self.provider_type, "tested_at": datetime.now(UTC).isoformat()}

    def publish(
        self,
        *,
        configuration: dict,
        title: str,
        html: str,
        slug: str,
        target_url: str,
        anchor_text: str,
        link_attribute: str = "standard",
    ) -> PublishResult:
        storage = get_storage_provider()
        prefix = (configuration.get("path_prefix") or "campaigns").strip("/")
        key = f"{prefix}/{safe_filename(slug)}/index.html"
        body = _inject_target_link(html, target_url=target_url, anchor_text=anchor_text, attribute=link_attribute)
        doc = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>{title}</title></head><body><article><h1>{title}</h1>{body}</article>"
            "<p><em>Published via authorized mock local provider. Not a ranking guarantee.</em></p>"
            "</body></html>"
        )
        storage.put_bytes(key, doc.encode("utf-8"), content_type="text/html")
        idx = int(configuration.get("mock_index") or 1)
        public = f"https://mock-source-{idx:03d}.local/{safe_filename(slug)}"
        return PublishResult(success=True, source_url=public, external_id=key, html_snapshot=doc)

    def unpublish(self, *, configuration: dict, external_id: str | None, source_url: str | None) -> dict:
        if external_id:
            try:
                get_storage_provider().delete(external_id)
            except Exception:
                pass
        return {"ok": True}

    def get_status(self, *, configuration: dict, source_url: str | None) -> dict:
        return {"ok": bool(source_url), "source_url": source_url}


class CloudStaticPublishingProvider(PublishingProvider):
    """Static HTML to authorized cloud/local object storage (S3-ready interface)."""

    provider_type = "cloud_static"

    def test(self, configuration: dict) -> dict:
        bucket = configuration.get("bucket") or settings.aws_s3_bucket or "local-campaign-bucket"
        return {
            "ok": True,
            "provider": self.provider_type,
            "bucket": bucket,
            "note": "Uses configured storage provider. Real AWS credentials stay server-side.",
        }

    def publish(
        self,
        *,
        configuration: dict,
        title: str,
        html: str,
        slug: str,
        target_url: str,
        anchor_text: str,
        link_attribute: str = "standard",
    ) -> PublishResult:
        # Until full S3 credentials are wired, write via local storage with cloud-like paths.
        storage = LocalStorageProvider()
        bucket = safe_filename(configuration.get("bucket") or "cloud-pages")
        key = f"cloud/{bucket}/{safe_filename(slug)}/index.html"
        body = _inject_target_link(html, target_url=target_url, anchor_text=anchor_text, attribute=link_attribute)
        css = "body{font-family:Georgia,serif;max-width:720px;margin:2rem auto;line-height:1.7}"
        css_key = f"cloud/{bucket}/{safe_filename(slug)}/assets/styles.css"
        storage.put_bytes(css_key, css.encode("utf-8"), content_type="text/css")
        doc = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>{title}</title>"
            f"<link rel='stylesheet' href='assets/styles.css' />"
            "</head><body><article>"
            f"<h1>{title}</h1>{body}</article></body></html>"
        )
        storage.put_bytes(key, doc.encode("utf-8"), content_type="text/html")
        base = (configuration.get("public_base_url") or "").rstrip("/")
        if base:
            source_url = f"{base}/{safe_filename(slug)}/"
        else:
            source_url = f"/api/v1/parasite-seo/backlink-campaigns/published-file/{key}"
        return PublishResult(success=True, source_url=source_url, external_id=key, html_snapshot=doc)

    def unpublish(self, *, configuration: dict, external_id: str | None, source_url: str | None) -> dict:
        if external_id:
            try:
                LocalStorageProvider().delete(external_id)
            except Exception:
                pass
        return {"ok": True}

    def get_status(self, *, configuration: dict, source_url: str | None) -> dict:
        return {"ok": bool(source_url), "source_url": source_url}


class WordPressStubProvider(PublishingProvider):
    """Stub for authorized WordPress — requires explicit credentials; does not publish without them."""

    provider_type = "wordpress"

    def test(self, configuration: dict) -> dict:
        if not configuration.get("site_url"):
            return {"ok": False, "error": "site_url required"}
        # Never auto-connect; credentials must be configured server-side.
        if not configuration.get("has_credentials"):
            return {
                "ok": False,
                "error": "WordPress credentials not configured. Connect an authorized site before publishing.",
            }
        return {"ok": True, "provider": self.provider_type}

    def publish(self, **kwargs) -> PublishResult:
        return PublishResult(
            success=False,
            source_url=None,
            error="WordPress publishing requires authorized credentials. Use mock_local or cloud_static in development.",
        )

    def unpublish(self, **kwargs) -> dict:
        return {"ok": False, "error": "Not configured"}

    def get_status(self, **kwargs) -> dict:
        return {"ok": False, "error": "Not configured"}


class GenericCMSProvider(PublishingProvider):
    """Authorized generic CMS — refuses publish without connected credentials."""

    provider_type = "generic_cms"

    def test(self, configuration: dict) -> dict:
        if not configuration.get("site_url") or not configuration.get("has_credentials"):
            return {"ok": False, "error": "Connect an authorized CMS before publishing."}
        return {"ok": True, "provider": self.provider_type}

    def publish(self, **kwargs) -> PublishResult:
        return PublishResult(success=False, source_url=None, error="Generic CMS requires authorized credentials.")

    def unpublish(self, **kwargs) -> dict:
        return {"ok": False, "error": "Not configured"}

    def get_status(self, **kwargs) -> dict:
        return {"ok": False, "error": "Not configured"}


class AWSProvider(CloudStaticPublishingProvider):
    provider_type = "aws_s3"


class AzureBlobProvider(CloudStaticPublishingProvider):
    provider_type = "azure_blob"


class GCSProvider(CloudStaticPublishingProvider):
    provider_type = "gcs"


PROVIDERS: dict[str, PublishingProvider] = {
    MockLocalPublishingProvider.provider_type: MockLocalPublishingProvider(),
    CloudStaticPublishingProvider.provider_type: CloudStaticPublishingProvider(),
    WordPressStubProvider.provider_type: WordPressStubProvider(),
    GenericCMSProvider.provider_type: GenericCMSProvider(),
    AWSProvider.provider_type: AWSProvider(),
    AzureBlobProvider.provider_type: AzureBlobProvider(),
    GCSProvider.provider_type: GCSProvider(),
}


def get_publishing_provider(provider_type: str) -> PublishingProvider:
    provider = PROVIDERS.get(provider_type)
    if not provider:
        raise ValueError(f"Unknown publishing provider: {provider_type}")
    return provider


def domain_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host or "unknown"
    except Exception:
        return "unknown"
