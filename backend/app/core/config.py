import os


class Settings:
    """Read once at import time. No pydantic-settings dependency for four values."""

    database_url: str = os.environ.get("DATABASE_URL", "")
    supabase_url: str = os.environ.get("SUPABASE_URL", "")
    supabase_service_key: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
    evidence_bucket: str = os.environ.get("EVIDENCE_BUCKET", "evidence")


settings = Settings()
