"""
Supabase Client — Singleton connection to Supabase for chat history persistence.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional

load_dotenv()

_client: Optional[Client] = None


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _client = create_client(url, key)
        print("[Supabase] Connected successfully")
    return _client
