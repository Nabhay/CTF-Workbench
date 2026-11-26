from __future__ import annotations


def blob_storage_key(sha256: str) -> str:
    """Application-controlled object key. Never derived from a user-supplied path."""
    digest = sha256.lower()
    return f"blobs/{digest[:2]}/{digest}"
