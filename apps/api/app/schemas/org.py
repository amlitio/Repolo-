"""Org/auth/RBAC/subscription/notification schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SessionUser(BaseModel):
    user_id: str
    org_id: str | None
    role: str
    email: str | None = None


class Organization(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    created_at: datetime
    updated_at: datetime


class RbacMe(BaseModel):
    user_id: str
    org_id: str | None
    role: str
    permissions: list[str]


class SubscriptionCreateRequest(BaseModel):
    county_fips: str | None = None
    property_id: str | None = None
    channel: str = Field(..., description="Delivery channel, e.g. 'email', 'sms', 'webhook'")
    alert_types: list[str] = Field(default_factory=list)


class Subscription(BaseModel):
    id: str
    user_id: str
    county_fips: str | None
    property_id: str | None
    channel: str
    alert_types: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NotificationTestResponse(BaseModel):
    status: str
    channel: str
    message: str
