"""Supabase client factory for backend usage.

The backend uses the Supabase **service role key**, which bypasses Row Level
Security. This is appropriate for server-side code where tenant isolation is
enforced in application logic (always filtering by ``company_id``).
"""

from functools import lru_cache

from supabase import Client, ClientOptions, create_client

from utils.config import get_settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client configured with the service role key.

    Raises:
        RuntimeError: If ``SUPABASE_URL`` or ``SUPABASE_SERVICE_ROLE_KEY``
            are missing from the environment.
    """
    settings = get_settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Supabase is not configured: set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in backend/.env"
        )

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
        options=ClientOptions(schema=settings.SUPABASE_SCHEMA),
    )
