"""SQLAlchemy ORM models.

Importing this package registers every model with `app.db.Base.metadata`,
which is required before `Base.metadata.create_all()` (used by tests and
`init_models()`) or Alembic's autogenerate can see the full schema.
"""

from app.models import (  # noqa: F401
    admin,
    alerts,
    flood,
    geo,
    org,
    procurement,
    risk,
    search,
    water,
    weather,
)

__all__ = [
    "admin",
    "alerts",
    "flood",
    "geo",
    "org",
    "procurement",
    "risk",
    "search",
    "water",
    "weather",
]
