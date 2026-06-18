"""Clerk JWT/JWKS verification, current-user dependency, and RBAC helpers.

Production auth flow: clients send `Authorization: Bearer <clerk-session-jwt>`.
We fetch (and cache) Clerk's JWKS, verify the RS256 signature, issuer, and
expiry, then expose the decoded claims as `CurrentUser`.

`AUTH_DEV_BYPASS` is an escape hatch for local dev/tests ONLY: when set, any
request is treated as authenticated with a synthetic admin user, with NO
signature verification. It defaults to off and logs a loud warning every time
it is actually used, so it can never be silently active in a deployed
environment.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx
import jwt
from fastapi import Depends, Request
from jwt import PyJWKClient

from app.config import Settings, get_settings
from app.core.errors import ForbiddenError, UnauthorizedError

logger = logging.getLogger("firip.auth")

_DEV_BYPASS_USER_ID = "dev-bypass-user"
_DEV_BYPASS_ORG_ID = "dev-bypass-org"


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    org_id: str | None
    role: str
    email: str | None = None
    permissions: tuple[str, ...] = ()


_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": ("read", "write", "admin"),
    "member": ("read", "write"),
    "viewer": ("read",),
}


def _permissions_for_role(role: str) -> tuple[str, ...]:
    return _ROLE_PERMISSIONS.get(role, ("read",))


class _JWKSClientCache:
    """Tiny TTL cache around PyJWKClient so we don't refetch JWKS per request."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._ttl = ttl_seconds
        self._client: PyJWKClient | None = None
        self._fetched_at: float = 0.0
        self._url: str | None = None

    def get(self, jwks_url: str) -> PyJWKClient:
        now = time.monotonic()
        if self._client is None or self._url != jwks_url or (now - self._fetched_at) > self._ttl:
            self._client = PyJWKClient(jwks_url)
            self._url = jwks_url
            self._fetched_at = now
        return self._client


_jwks_cache = _JWKSClientCache()


def _decode_clerk_token(token: str, settings: Settings) -> dict:
    if not settings.clerk_jwks_url:
        raise UnauthorizedError("Auth is not configured (missing CLERK_JWKS_URL)")
    try:
        jwks_client = _jwks_cache.get(settings.clerk_jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        options = {"verify_aud": bool(settings.clerk_audience)}
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.clerk_audience if settings.clerk_audience else None,
            issuer=settings.clerk_issuer if settings.clerk_issuer else None,
            options=options,
        )
    except httpx.HTTPError as exc:
        raise UnauthorizedError("Could not reach auth provider to verify token") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired authentication token") from exc
    return claims


def get_current_user(request: Request) -> CurrentUser:
    """FastAPI dependency: verifies the bearer token and returns CurrentUser.

    Raises UnauthorizedError (-> 401) if missing/invalid, never silently
    proceeds unauthenticated.
    """

    settings = get_settings()

    if settings.auth_dev_bypass:
        logger.warning(
            "AUTH_DEV_BYPASS is enabled - all requests are being treated as an "
            "authenticated admin user with NO token verification. This must "
            "NEVER be set in a deployed environment."
        )
        return CurrentUser(
            user_id=_DEV_BYPASS_USER_ID,
            org_id=_DEV_BYPASS_ORG_ID,
            role="admin",
            email="dev-bypass@firip.local",
            permissions=_permissions_for_role("admin"),
        )

    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise UnauthorizedError("Missing bearer token")

    claims = _decode_clerk_token(token, settings)
    user_id = claims.get("sub")
    if not user_id:
        raise UnauthorizedError("Token missing subject claim")
    org_id = claims.get("org_id")
    role = claims.get("org_role") or claims.get("role") or "member"
    # Clerk org roles are sometimes prefixed like "org:admin".
    role = role.split(":")[-1] if isinstance(role, str) else "member"
    email = claims.get("email")
    return CurrentUser(
        user_id=user_id,
        org_id=org_id,
        role=role,
        email=email,
        permissions=_permissions_for_role(role),
    )


def require_role(*allowed_roles: str):
    """FastAPI dependency factory: 403s unless the current user's role is in
    `allowed_roles`. Use `require_role("admin")` for admin-only routes."""

    def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                f"Role '{current_user.role}' is not permitted to access this resource"
            )
        return current_user

    return _dependency


require_admin = require_role("admin")
