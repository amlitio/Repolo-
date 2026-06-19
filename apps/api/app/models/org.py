"""Organizations, users, memberships, roles, audit logs."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin, new_uuid
from app.models.types import GUID


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    clerk_org_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")

    memberships: Mapped[list[Membership]] = relationship(back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    clerk_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    memberships: Mapped[list[Membership]] = relationship(back_populates="user")


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(GUID(), ForeignKey("organizations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(back_populates="memberships")


class Role(Base, TimestampMixin):
    """Named permission sets, e.g. 'admin', 'member', 'viewer'."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    permissions: Mapped[list[str]] = mapped_column(Text, nullable=False, default="[]")  # JSON-encoded list


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    actor_user_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("organizations.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    county_fips: Mapped[str | None] = mapped_column(String(5), nullable=True)
    property_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("properties.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # email | sms | webhook
    alert_types: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON-encoded list
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    subscription_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("subscriptions.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="simulated")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
