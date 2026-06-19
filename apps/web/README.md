# @firip/web

FIRIP web frontend: the Florida flood/water risk intelligence map workspace,
role-based dashboards, and admin console. Next.js 16 App Router, TypeScript
(strict), Tailwind CSS v4, hand-written Radix-based UI primitives, Mapbox GL
JS v3, Clerk auth, React Query, and Zod for runtime API validation.

This app is part of the FIRIP npm-workspaces monorepo and depends on the
internal `@firip/shared` package (types, scoring constants, and the FL
county/source registry) - see `../../packages/shared`.

## Setup

From the **repo root** (not `apps/web/`):

```bash
npm install
npm run build --workspace=packages/shared   # only needed if packages/shared/dist is missing/stale
```

`npm install` links `@firip/shared` into `apps/web/node_modules` via npm
workspaces because both packages are listed in the root `package.json`
`workspaces` array.

Copy the env template and fill in real values for local development:

```bash
cp apps/web/.env.example apps/web/.env.local
```

| Variable | Required for | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | all data fetching | FastAPI backend base URL, no trailing slash |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | map tiles | without it, `MapCanvas` renders a "Set NEXT_PUBLIC_MAPBOX_TOKEN to load the map" placeholder instead of crashing |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` | auth | without them, `middleware.ts` and `ClerkProvider` become no-ops so `/map`, `/dashboard/*`, `/admin` are unprotected locally |
| `NEXT_PUBLIC_POSTHOG_KEY` / `NEXT_PUBLIC_POSTHOG_HOST` | product analytics | optional, not yet wired into a provider |
| `NEXT_PUBLIC_SENTRY_DSN` | error monitoring | optional, not yet wired into a provider |

## Running the dev server

```bash
npm run dev --workspace=apps/web
# or, from apps/web/:
npm run dev
```

Serves on `http://localhost:3000`. Requires a running `apps/api` (FastAPI
backend) at `NEXT_PUBLIC_API_URL` for any page beyond the static landing
page to show real data; without it, every data view renders its loading
state and then its error/empty state (by design - see "Known limitations").

## Scripts

| Script | Purpose |
|---|---|
| `npm run dev` | Next.js dev server |
| `npm run build` | Production build (`next build`, standalone output) |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint (`next/core-web-vitals` + `next/typescript`) |
| `npm run typecheck` | `tsc --noEmit` against the app tsconfig |
| `npm run test` | Vitest unit/component tests (jsdom + React Testing Library) |
| `npm run test:e2e` | Playwright e2e specs (see below) |

All of the above are also reachable from the repo root via the aggregate
scripts (`npm run dev:web`, `npm run lint`, `npm run typecheck`, `npm run
test`, `npm run test:e2e`, `npm run build`), which delegate to this
workspace with `--workspace=apps/web`.

## Running Playwright e2e against a real backend

The specs under `e2e/` are written to run against a **live dev server +
live `apps/api`** (and, for the auth-gated specs, a live Clerk test
instance). They are not executed as part of `npm run test` and do not need
`npx playwright install` to have been run for the rest of the toolchain
(build/lint/typecheck/unit tests) to pass.

To actually run them:

```bash
npx playwright install --with-deps chromium   # one-time browser install
npm run dev --workspace=apps/api &             # start the backend (see apps/api/README)
npm run dev --workspace=apps/web &              # start this app
npm run test:e2e --workspace=apps/web
```

- `e2e/login.spec.ts` - sign-in redirect and (optionally, if
  `E2E_TEST_USER_EMAIL`/`E2E_TEST_USER_PASSWORD` are set against a Clerk test
  instance) full sign-in flow.
- `e2e/map-layers.spec.ts` - `/map` workspace layout, layer manager load +
  toggle, event timeline drawer.
- `e2e/county-search.spec.ts` - county search results and risk lookup via
  the intelligence panel.
- `e2e/property-risk.spec.ts` - dashboard county risk widget render.
- `e2e/alert-subscription.spec.ts` - subscribing to county alerts and
  sending a test notification (requires an authenticated session).

`playwright.config.ts` will auto-start `npm run dev` as its webServer unless
`PLAYWRIGHT_SKIP_WEBSERVER` is set (useful if you already have a dev server
running) or `PLAYWRIGHT_BASE_URL` points elsewhere (e.g. a deployed preview).

Because these specs need real services, they were validated here only via
`npx tsc -p tsconfig.e2e.json --noEmit` (syntactic/type correctness), not a
live run - that is expected for this sandbox.

## Architecture notes

- **API client** (`lib/api/client.ts`): a typed `apiFetch<T>` wrapper. Success
  responses from `apps/api` are the bare resource (HTTP 200/201, no
  envelope) and are returned as `T` directly. Failure responses always match
  `ApiErrorResponse` from `@firip/shared`
  (`{success:false, error:{code,message,details}}`); `apiFetch` parses that
  envelope and throws a flat `ApiClientError {code, message, details,
  status}` so call sites and React Query error boundaries don't re-parse
  JSON.
- **Endpoints** (`lib/api/endpoints.ts`): one typed function per backend
  route in the contract, each validating the response shape with a Zod
  schema from `lib/api/schemas.ts` before returning. This catches
  backend/frontend drift at the client boundary instead of letting malformed
  data silently reach React state - useful since `apps/api` is being built
  independently against the same written contract.
- **Hooks** (`lib/hooks/*`): one React Query hook per endpoint (or small
  group), with a centralized query-key factory (`lib/hooks/queryKeys.ts`) so
  cache invalidation (e.g. after creating a subscription) stays consistent.
- **Map** (`components/map/*`): `MapCanvas` lazy-loads `mapbox-gl` client-side
  only and degrades to a placeholder when `NEXT_PUBLIC_MAPBOX_TOKEN` is
  unset or initialization fails - this is required behavior, not a
  workaround, since the contract calls for the map to never crash without a
  token. `LayerManager` toggles are driven entirely by `GET /map/layers`
  data (no hardcoded layer list beyond the shared `MAP_LAYER_IDS` constants
  used for typing). `IntelligencePanel` shows property/county risk +
  explanation for the current map search selection. `EventTimelineDrawer` is
  a collapsible bottom panel of active alerts. `SearchBar` combines
  county/city/property search and a natural-language research ask box.
- **Risk grade colors** (`lib/utils/risk.ts`): derived once from the shared
  `RiskGrade` union (`A`-`F`) so the map legend, dashboards, and
  intelligence panel can never drift into a second color scale.
- **Auth** (`middleware.ts`, `app/layout.tsx`): Clerk route protection for
  `/map`, `/dashboard/*`, `/admin`. Both the middleware and the root layout's
  `ClerkProvider` wrap become no-ops when Clerk env vars are absent, so
  `next build`/`next dev` never hard-depend on reaching Clerk - required for
  this build environment, and generally good behavior for a fresh checkout
  before secrets are provisioned.
- **No build-time network calls**: nothing in `app/` performs a server-side
  or static-generation-time fetch to `apps/api`, Clerk, or Mapbox. All data
  fetching is client-side via React Query hooks (`"use client"` components),
  and `next/font/google` is intentionally not used (system font stack via
  Tailwind's `font-sans`/`font-mono` instead) - both because this sandbox
  has no egress to those hosts, and because it's the correct architecture
  for a dashboard whose data is inherently per-session/per-org.

## Known limitations

- **Map tiles will not render without a real Mapbox token.** Set
  `NEXT_PUBLIC_MAPBOX_TOKEN` to a real Mapbox GL JS public token to see
  actual tiles; without it (or without network access to
  `api.mapbox.com`), `MapCanvas` shows a clear placeholder by design rather
  than crashing.
- **All live data requires a running `apps/api`.** Every dashboard widget,
  the layer manager, search, and the admin console call the FastAPI backend
  via `NEXT_PUBLIC_API_URL`; without it, they show their loading state
  followed by an error state with a retry button (no hardcoded fake
  numbers anywhere).
- **`/procurement/opportunities` may legitimately return an empty page**
  while backend ingestion is pending - `ProcurementWidget` renders an empty
  state ("Procurement ingestion is pending for this view") rather than
  treating that as an error.
- **Admin console requires the `admin` RBAC role** from `GET /rbac/me`;
  any other role (or a failed/absent session) renders an "Insufficient
  permissions" state rather than the admin tables.
- **Playwright specs are not executed in this build/CI sandbox** - no live
  backend, Clerk, or Mapbox network access here. They are syntactically
  validated (`npx tsc -p tsconfig.e2e.json --noEmit`) and use realistic
  role/label selectors, but should be run against a real local or staging
  stack to get a pass/fail signal.
- **PostHog and Sentry env vars are defined but not yet wired** to an actual
  provider/init call in this MVP slice; they're reserved for a follow-up
  observability pass.

## Directory layout

```
app/                  Next.js App Router routes (landing, sign-in/up, map, dashboard/[role], admin)
components/ui/        Hand-written Radix + Tailwind primitives (Button, Card, Tabs, Dialog, Badge, Input, Tooltip, Sheet)
components/map/       MapCanvas, LayerManager, IntelligencePanel, EventTimelineDrawer, SearchBar
components/dashboards/ Per-role dashboard widgets
lib/api/               Typed fetch client, one function per backend route, Zod schemas
lib/hooks/              React Query hooks wrapping lib/api
lib/providers/          QueryClientProvider
lib/utils/              cn() class merge helper, risk grade color mapping
tests/                  Vitest + React Testing Library
e2e/                    Playwright specs (see above)
```
