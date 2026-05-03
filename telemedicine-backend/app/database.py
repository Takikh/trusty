"""
Supabase PostgREST client initialisation.

Uses the SERVICE KEY so that this backend bypasses Row-Level Security
and has full read/write access to all tables.

The postgrest client provides the same `.from_().select().execute()` API
as the full supabase client, but without the heavy storage/auth/realtime
sub-packages that have build issues on Python 3.14.

Usage anywhere in the app:
    from app.database import rest
    result = rest.from_("users").select("*").execute()
"""

import httpx
from postgrest import SyncPostgrestClient

from app.config import settings

# Supabase REST API endpoint is always at /rest/v1
_rest_url = f"{settings.supabase_url}/rest/v1"

# Force HTTP/1.1 to avoid h2 connection reset issues on Windows
_http_client = httpx.Client(http2=False)

rest = SyncPostgrestClient(
    base_url=_rest_url,
    headers={
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
    },
    http_client=_http_client,
)
