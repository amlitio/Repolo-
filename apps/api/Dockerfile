# FIRIP API - multi-stage build for the apps/api FastAPI backend.
# Build context MUST be the monorepo root (not apps/api), since app/config.py
# reads packages/shared/data/*.json (counties/sources/scoring registries) at
# startup, e.g.:
#   docker build -f apps/api/Dockerfile -t firip-api .
#
# Runtime config (DATABASE_URL, Clerk keys, connector API keys, etc.) is read
# from process env at request time - see apps/api/.env.example. Nothing
# secret is baked into the image.

FROM python:3.11-slim AS base
WORKDIR /repo
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ---- deps: install Python dependencies --------------------------------------
FROM base AS deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY apps/api/requirements.txt apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt

# ---- runtime: app code + shared data registry --------------------------------
FROM base AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY apps/api/app apps/api/app
COPY apps/api/alembic apps/api/alembic
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY packages/shared/data packages/shared/data

WORKDIR /repo/apps/api
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
