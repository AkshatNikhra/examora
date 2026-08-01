"""Cloudflare R2 (S3-compatible) storage helpers."""

from __future__ import annotations

import boto3
from botocore.client import BaseClient
from fastapi import HTTPException, status

from app.core.config import settings


def get_r2_client() -> BaseClient:
    if not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="R2 credentials are not configured",
        )
    endpoint = settings.r2_endpoint
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="R2 endpoint is not configured",
        )

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def upload_pdf(*, key: str, body: bytes, content_type: str = "application/pdf") -> str:
    """Upload PDF bytes to R2 and return the object key."""
    client = get_r2_client()
    try:
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload file to R2: {exc}",
        ) from exc
    return key


def download_pdf(*, key: str) -> bytes:
    """Download PDF bytes from R2 by object key."""
    client = get_r2_client()
    try:
        response = client.get_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        body = response["Body"].read()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to download file from R2: {exc}",
        ) from exc
    if not body:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Downloaded PDF from R2 was empty",
        )
    return body
