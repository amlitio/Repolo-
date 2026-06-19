# FIRIP Workers - ingestion/agent scheduler (apps/workers).
# Build context MUST be the monorepo root (not apps/workers), e.g.:
#   docker build -f apps/workers/Dockerfile -t firip-workers .
#
# apps/workers/requirements.txt installs apps/api as an EDITABLE package
# (`-e ../api`) so this image reuses app.* (connectors/models/db/scoring)
# rather than duplicating it - see requirements.txt's own comment. An
# editable install records a path reference back to apps/api's source tree,
# so (unlike apps/api/Dockerfile's copy-only-site-packages multi-stage
# build) this image must keep that source tree present at the same path at
# runtime; there is no separate deps-only stage to copy from.
#
# Runtime config (DATABASE_URL, connector API keys, OPENAI/GEMINI keys,
# etc.) is read from process env at run time - see apps/workers/.env.example.
# Nothing secret is baked into the image.

FROM python:3.11-slim
WORKDIR /repo
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY apps/api apps/api
COPY apps/workers apps/workers
COPY packages/shared/data packages/shared/data

WORKDIR /repo/apps/workers
RUN pip install --no-cache-dir -r requirements.txt

ENV ENVIRONMENT=production
CMD ["python", "-m", "worker.scheduler"]
