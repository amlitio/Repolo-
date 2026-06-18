"""Auth/session, organizations, and RBAC introspection endpoints. All
require a verified Clerk session."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models.org import Membership, Organization
from app.schemas.common import Paginated
from app.schemas.org import Organization as OrganizationSchema
from app.schemas.org import RbacMe, SessionUser

router = APIRouter(tags=["auth"])


@router.get(
    "/auth/session",
    response_model=SessionUser,
    summary="Current authenticated session",
    description="Returns the current user's identity from their verified Clerk token. 401 if absent/invalid.",
)
async def get_session(current_user: CurrentUser = Depends(get_current_user)) -> SessionUser:
    return SessionUser(
        user_id=current_user.user_id,
        org_id=current_user.org_id,
        role=current_user.role,
        email=current_user.email,
    )


@router.get(
    "/orgs",
    response_model=Paginated[OrganizationSchema],
    summary="List organizations for the current user",
)
async def list_orgs(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
) -> Paginated[OrganizationSchema]:
    stmt = (
        select(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == current_user.user_id)
    )
    result = await db.execute(stmt)
    orgs = result.scalars().all()
    total = len(orgs)
    start = (page - 1) * page_size
    page_items = orgs[start : start + page_size]
    return Paginated[OrganizationSchema](
        items=[OrganizationSchema.model_validate(o) for o in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/rbac/me",
    response_model=RbacMe,
    summary="Current user's role and permissions",
)
async def rbac_me(current_user: CurrentUser = Depends(get_current_user)) -> RbacMe:
    return RbacMe(
        user_id=current_user.user_id,
        org_id=current_user.org_id,
        role=current_user.role,
        permissions=list(current_user.permissions),
    )
