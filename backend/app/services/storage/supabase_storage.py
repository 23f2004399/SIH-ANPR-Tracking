"""Evidence storage: private bucket, signed URLs — separate from the public
`videos` bucket the old dashboard streams from. Vehicle crops and plate crops
are not meant to be publicly reachable.

Uses the Storage REST API directly (same approach as db/upload_videos.py)
rather than the supabase-py client, so this has no extra dependency.
"""

import requests

from backend.app.core.config import settings


def _headers(content_type: str | None = None) -> dict:
    h = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def upload_bytes(path: str, data: bytes, content_type: str) -> None:
    url = f"{settings.supabase_url}/storage/v1/object/{settings.evidence_bucket}/{path}"
    resp = requests.post(url, data=data, headers={**_headers(content_type), "x-upsert": "true"}, timeout=60)
    resp.raise_for_status()


def create_signed_url(path: str, expires_in: int = 3600) -> str:
    url = f"{settings.supabase_url}/storage/v1/object/sign/{settings.evidence_bucket}/{path}"
    resp = requests.post(url, json={"expiresIn": expires_in}, headers=_headers("application/json"), timeout=30)
    resp.raise_for_status()
    return f"{settings.supabase_url}/storage/v1{resp.json()['signedURL']}"
