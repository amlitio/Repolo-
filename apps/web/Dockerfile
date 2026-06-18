# FIRIP web frontend - multi-stage build for the apps/web Next.js 16 app.
# Build context MUST be the monorepo root (not apps/web), since this app
# depends on the @firip/shared workspace package, e.g.:
#   docker build -f apps/web/Dockerfile -t firip-web .
#
# Build-time note: this build performs zero network calls to the FastAPI
# backend, Clerk, or Mapbox - `next build` only needs NODE_ENV=production
# and the npm registry (for `npm ci`). Runtime env vars (NEXT_PUBLIC_API_URL,
# Mapbox/Clerk keys) are read at request time, not baked into the build,
# except for NEXT_PUBLIC_* values which Next.js inlines at build time if
# present - pass them as --build-arg if you need a token baked in.

FROM node:22-slim AS base
WORKDIR /repo

# ---- deps: install full workspace dependency graph -------------------------
FROM base AS deps
COPY package.json package-lock.json ./
COPY packages/shared/package.json packages/shared/package.json
COPY apps/web/package.json apps/web/package.json
RUN npm ci

# ---- build: compile @firip/shared, then next build -------------------------
FROM base AS build
COPY --from=deps /repo/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY packages/shared packages/shared
COPY apps/web apps/web
RUN npm run build --workspace=packages/shared
ENV NODE_ENV=production
RUN npm run build --workspace=apps/web

# ---- runtime: standalone Next.js server -------------------------------------
FROM base AS runtime
ENV NODE_ENV=production
ENV PORT=3000
WORKDIR /repo/apps/web

COPY --from=build /repo/apps/web/public ./public
COPY --from=build /repo/apps/web/.next/standalone ./
COPY --from=build /repo/apps/web/.next/static ./apps/web/.next/static

EXPOSE 3000
CMD ["node", "apps/web/server.js"]
