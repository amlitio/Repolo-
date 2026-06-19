"""Just-in-time provisioning of internal `User`/`Organization` rows from a
verified Clerk identity.

`CurrentUser.user_id` / `CurrentUser.org_id` (see app/core/auth.py) are
Clerk's raw `sub` / `org_id` claims - opaque Clerk-format strings (e.g.
"user_2abc123"), NOT our internal UUID primary keys. Several tables
(`memberships`, `subscriptions`, `audit_logs`, ...) store foreign keys typed
as our internal GUID columns, so any code path that writes one of those rows
on behalf of the current request must first resolve the Clerk identity to an
internal `users.id` / `organizations.id` - never write the raw Clerk id into
a GUID column (it is not a UUID and will fail to bind, or worse, silently
collide with an unrelated row on a backend that doesn't validate UUID shape).

This module does that resolution, creating the row on first sight (Clerk is
the source of truth for identity; we mirror it lazily rather than requiring
a separate sync webhook in this MVP).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.models.org import Organization, User


async def ensure_user(db: AsyncSession, current_user: CurrentUser) -> User:
    """Get-or-create the internal `User` row for this Clerk identity."""
    result = await db.execute(select(User).where(User.clerk_user_id == current_user.user_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    email = current_user.email or f"{current_user.user_id}@unknown.firip.local"
    user = User(clerk_user_id=current_user.user_id, email=email)
    db.add(user)
    await db.flush()
    return user


async def ensure_organization(db: AsyncSession, current_user: CurrentUser) -> Organization | None:
    """Get-or-create the internal `Organization` row for this Clerk org, if any.

    Returns None if the current session has no org context (Clerk supports
    personal/org-less sessions), in which case org-scoped foreign keys should
    be left null rather than fabricating an organization.
    """
    if not current_user.org_id:
        return None

    result = await db.execute(select(Organization).where(Organization.clerk_org_id == current_user.org_id))
    org = result.scalar_one_or_none()
    if org is not None:
        return org

    org = Organization(
        clerk_org_id=current_user.org_id,
        name=current_user.org_id,
        slug=current_user.org_id,
    )
    db.add(org)
    await db.flush()
    return org


async def ensure_user_and_org(
    db: AsyncSession, current_user: CurrentUser
) -> tuple[User, Organization | None]:
    """Convenience wrapper resolving both the internal user and (optional) org row."""
    user = await ensure_user(db, current_user)
    org = await ensure_organization(db, current_user)
    return user, org
