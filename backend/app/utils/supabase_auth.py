"""
Supabase JWT verification helpers.
"""
from __future__ import annotations

import time
from typing import Any, Dict

import requests
from jose import jwt


class SupabaseJWTError(Exception):
    pass


_JWKS_CACHE: Dict[str, Any] = {
    "keys": [],
    "fetched_at": 0.0,
}
_JWKS_TTL_SECONDS = 3600


def _normalize_supabase_url(url: str) -> str:
    return url.rstrip("/")


def _fetch_jwks(supabase_url: str) -> Dict[str, Any]:
    supabase_url = _normalize_supabase_url(supabase_url)
    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    response = requests.get(jwks_url, timeout=10)
    response.raise_for_status()
    return response.json()


def _get_jwks(supabase_url: str) -> Dict[str, Any]:
    now = time.time()
    if _JWKS_CACHE["keys"] and (now - _JWKS_CACHE["fetched_at"] < _JWKS_TTL_SECONDS):
        return _JWKS_CACHE

    jwks = _fetch_jwks(supabase_url)
    _JWKS_CACHE["keys"] = jwks.get("keys", [])
    _JWKS_CACHE["fetched_at"] = now
    return _JWKS_CACHE


def verify_supabase_jwt(token: str, supabase_url: str, audience: str = "authenticated") -> Dict[str, Any]:
    if not supabase_url:
        raise SupabaseJWTError("Supabase URL not configured")

    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise SupabaseJWTError("Invalid token header") from exc

    kid = header.get("kid")
    if not kid:
        raise SupabaseJWTError("Token missing kid header")

    jwks = _get_jwks(supabase_url)
    keys = jwks.get("keys", [])
    key = next((k for k in keys if k.get("kid") == kid), None)

    if key is None:
        # Refresh JWKS once if key not found
        jwks = _fetch_jwks(supabase_url)
        keys = jwks.get("keys", [])
        key = next((k for k in keys if k.get("kid") == kid), None)
        if key is None:
            raise SupabaseJWTError("No matching JWK for token kid")

    issuer = f"{_normalize_supabase_url(supabase_url)}/auth/v1"

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )
        return payload
    except Exception as exc:
        raise SupabaseJWTError("Supabase token verification failed") from exc
