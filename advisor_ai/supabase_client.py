"""
Supabase Client — Singleton connection to Supabase for chat history persistence.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Any, Dict, Optional

load_dotenv()

_client: Optional[Client] = None


def _env(name: str) -> Optional[str]:
    """Read an environment variable and trim deployment-input whitespace."""
    value = os.getenv(name)
    return value.strip() if value else None


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        url = _env("SUPABASE_URL")
        key = _env("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _client = create_client(url, key)
        print("[Supabase] Client initialized")
    return _client


def supabase_status() -> Dict[str, Any]:
    """Return Supabase configuration and connectivity status without exposing secrets."""
    url = _env("SUPABASE_URL")
    key = _env("SUPABASE_KEY")
    status: Dict[str, Any] = {
        "configured": bool(url and key),
        "connected": False,
        "url_configured": bool(url),
        "key_configured": bool(key),
        "last_error": None,
    }
    if not status["configured"]:
        status["last_error"] = "SUPABASE_URL and SUPABASE_KEY must be set."
        return status

    try:
        client = get_supabase()
        client.table("sessions").select("session_id").limit(1).execute()
        status["connected"] = True
    except Exception as e:
        status["last_error"] = str(e)
    return status
