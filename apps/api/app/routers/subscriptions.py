"""Alert subscription management and notification test-send. All routes
require a verified Clerk session.

Notifications are never actually delivered to a third-party provider in this
MVP unless NOTIFICATIONS_PROVIDER/NOTIFICATIONS_API_KEY are configured; when
they are not, /notifications/test honestly reports a "simulated" status
rather than claiming a real send happened. Every notification test-send is
audit-logged regardless of whether it was simulated or real.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.audit import record_audit_log
from app.core.auth import CurrentUser, get_current_user
from app.core.errors import NotFoundError
from app.core.provisioning import ensure_user_and_org
from app.db import get_db
from app.models.org import Notification, Subscription as SubscriptionModel
from app.models.types import is_valid_guid
from app.schemas.common import Paginated
from app.schemas.org import (
    NotificationTestResponse,
    Subscription,
    SubscriptionCreateRequest,
)

router = APIRouter(tags=["subscriptions"])


def _to_schema(model: SubscriptionModel) -> Subscription:
    return Subscription(
        id=model.id,
        user_id=model.user_id,
        county_fips=model.county_fips,
        property_id=model.property_id,
        channel=model.channel,
        alert_types=json.loads(model.alert_types),
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.get(
    "/subscriptions",
    response_model=Paginated[Subscription],
    summary="List the current user's alert subscriptions",
)
async def list_subscriptions(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Paginated[Subscription]:
    user, _org = await ensure_user_and_org(db, current_user)
    await db.commit()
    result = await db.execute(select(SubscriptionModel).where(SubscriptionModel.user_id == user.id))
    rows = result.scalars().all()
    total = len(rows)
    start = (page - 1) * page_size
    page_items = rows[start : start + page_size]
    return Paginated[Subscription](
        items=[_to_schema(s) for s in page_items], total=total, page=page, page_size=page_size
    )


@router.post(
    "/subscriptions",
    response_model=Subscription,
    summary="Create an alert subscription",
)
async def create_subscription(
    payload: SubscriptionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    user, org = await ensure_user_and_org(db, current_user)
    subscription = SubscriptionModel(
        user_id=user.id,
        county_fips=payload.county_fips,
        property_id=payload.property_id,
        channel=payload.channel,
        alert_types=json.dumps(payload.alert_types),
        is_active=True,
    )
    db.add(subscription)
    await db.flush()
    await record_audit_log(
        db,
        actor_user_id=user.id,
        organization_id=org.id if org else None,
        action="subscription.create",
        resource_type="subscription",
        resource_id=subscription.id,
        metadata={"channel": payload.channel, "county_fips": payload.county_fips},
    )
    await db.commit()
    await db.refresh(subscription)
    return _to_schema(subscription)


@router.post(
    "/notifications/test",
    response_model=NotificationTestResponse,
    summary="Send a test notification on a given channel",
    description="If NOTIFICATIONS_PROVIDER/NOTIFICATIONS_API_KEY are not configured in this "
    "environment, honestly reports status='simulated' rather than claiming a real delivery. "
    "Always audit-logged.",
)
async def test_notification(
    channel: str = Query(..., description="Delivery channel, e.g. 'email', 'sms', 'webhook'"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationTestResponse:
    user, org = await ensure_user_and_org(db, current_user)
    settings = get_settings()
    is_configured = bool(settings.notifications_provider and settings.notifications_api_key)
    status_value = "simulated"
    message = (
        f"No notification provider is configured in this environment; a real '{channel}' "
        "notification was NOT sent. This is a simulated test record only."
    )
    if is_configured:
        # This MVP does not implement a real outbound notification send path
        # synchronously inside the API process (mirrors the /research/ask
        # design: real delivery is left to the worker process so retries and
        # provider failures are handled in one place). Still honestly report
        # this rather than claiming delivery succeeded.
        status_value = "provider_configured_not_sent"
        message = (
            f"A notification provider is configured, but this MVP's API process does not send "
            f"'{channel}' notifications synchronously; delivery is handled out-of-band by "
            "apps/workers. No message was actually sent."
        )

    notification = Notification(
        user_id=user.id,
        subscription_id=None,
        channel=channel,
        subject="FIRIP test notification",
        body=message,
        status=status_value,
    )
    db.add(notification)
    await db.flush()
    await record_audit_log(
        db,
        actor_user_id=user.id,
        organization_id=org.id if org else None,
        action="notification.test",
        resource_type="notification",
        resource_id=notification.id,
        metadata={"channel": channel, "status": status_value},
    )
    await db.commit()

    return NotificationTestResponse(status=status_value, channel=channel, message=message)


@router.delete(
    "/subscriptions/{subscription_id}",
    response_model=Subscription,
    summary="Deactivate an alert subscription",
)
async def delete_subscription(
    subscription_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    if not is_valid_guid(subscription_id):
        raise NotFoundError(f"No subscription found with id '{subscription_id}' for the current user")

    user, org = await ensure_user_and_org(db, current_user)
    result = await db.execute(
        select(SubscriptionModel).where(
            SubscriptionModel.id == subscription_id,
            SubscriptionModel.user_id == user.id,
        )
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise NotFoundError(f"No subscription found with id '{subscription_id}' for the current user")

    subscription.is_active = False
    await record_audit_log(
        db,
        actor_user_id=user.id,
        organization_id=org.id if org else None,
        action="subscription.deactivate",
        resource_type="subscription",
        resource_id=subscription.id,
    )
    await db.commit()
    await db.refresh(subscription)
    return _to_schema(subscription)
