"""Storage abstraction — local now, S3-ready later. No AWS logic in content services."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings


SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def safe_filename(name: str, *, default: str = "file") -> str:
    cleaned = SAFE_NAME_RE.sub("-", (name or default).strip()).strip(".-")
    cleaned = cleaned.replace("..", ".")
    return (cleaned or default)[:180]


class StorageProvider(ABC):
    @abstractmethod
    def put_bytes(self, key: str, data: bytes, *, content_type: str) -> str:
        """Store bytes; return opaque storage_key."""

    @abstractmethod
    def get_bytes(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def public_url(self, key: str) -> str | None:
        """Optional URL for downloads; never expose absolute filesystem paths to clients."""


class LocalStorageProvider(StorageProvider):
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(settings.local_storage_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Prevent path traversal
        safe_key = key.replace("\\", "/").lstrip("/")
        if ".." in safe_key.split("/"):
            raise ValueError("Invalid storage key")
        path = (self.root / safe_key).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        return path

    def put_bytes(self, key: str, data: bytes, *, content_type: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def public_url(self, key: str) -> str | None:
        # Served only via authenticated export download endpoints — not a public FS path.
        return f"storage://{key}"


class S3StorageProvider(StorageProvider):
    """Placeholder for Phase 6+ object storage. Not used until credentials are configured."""

    def put_bytes(self, key: str, data: bytes, *, content_type: str) -> str:
        raise NotImplementedError("S3 storage is not configured in Phase 5")

    def get_bytes(self, key: str) -> bytes:
        raise NotImplementedError("S3 storage is not configured in Phase 5")

    def delete(self, key: str) -> None:
        raise NotImplementedError("S3 storage is not configured in Phase 5")

    def public_url(self, key: str) -> str | None:
        return None


def get_storage_provider() -> StorageProvider:
    if settings.aws_s3_bucket and settings.aws_access_key_id and settings.aws_secret_access_key:
        # Keep interface ready; Phase 5 defaults to local until S3 provider is fully wired.
        return LocalStorageProvider()
    return LocalStorageProvider()
