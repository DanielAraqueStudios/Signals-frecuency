"""S3-compatible object storage for captured images.

Deliberately vendor-agnostic (boto3 + a custom endpoint_url): works
against AWS S3, Cloudflare R2, Backblaze B2, or a local MinIO container
for dev -- Railway has no first-party object storage.
"""

from __future__ import annotations

import uuid

import boto3

from app.config import settings

_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
)


def upload_image(user_id: str, content: bytes, content_type: str) -> str:
    """Uploads image bytes and returns the storage key."""
    key = f"{user_id}/{uuid.uuid4()}.jpg"
    _client.put_object(Bucket=settings.s3_bucket, Key=key, Body=content, ContentType=content_type)
    return key


def ensure_bucket_exists() -> None:
    """Idempotently creates the bucket -- convenient for local dev against
    MinIO, where nothing provisions it ahead of time. In production this
    is a no-op if the bucket already exists (most S3-compatible providers
    return a recoverable error we swallow here for exactly that reason)."""
    try:
        _client.create_bucket(Bucket=settings.s3_bucket)
    except Exception:  # noqa: BLE001 - provider-specific "already exists" errors vary
        pass
