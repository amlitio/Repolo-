# Vercel deployment

`apps/web` (Next.js 16) deploys to Vercel. Because this is an npm-workspaces
monorepo where `apps/web` depends on `@firip/shared` (built from
`packages/shared`), the build must happen from the repo root, not from
inside `apps/web`.

## Setup

1. In the Vercel project settings, set **Root Directory** to `apps/web`
   and enable "Include source files outside of the Root Directory" (Vercel
   needs `packages/shared` to install/build the workspace dependency).
2. Copy `infra/vercel/vercel.json` to `apps/web/vercel.json`, or paste its
   `buildCommand`/`installCommand` into the dashboard's build settings —
   Vercel only reads `vercel.json` from the configured Root Directory.
3. Set environment variables from `apps/web/.env.example`:
   `NEXT_PUBLIC_API_URL` (the deployed `apps/api` URL),
   `NEXT_PUBLIC_MAPBOX_TOKEN`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`,
   `CLERK_SECRET_KEY`, and optionally the PostHog/Sentry keys.
4. Deploy. The app intentionally renders without crashing if Mapbox/Clerk
   env vars are absent (graceful placeholders), so a first deploy without
   secrets configured will still build and serve a landing page — useful
   for verifying the pipeline before secrets are provisioned.

## Notes

- Never tested against a live Vercel project in the sandbox this repo was
  built in (no network access to vercel.com). Validate the build/install
  command override actually resolves `@firip/shared` correctly on a real
  Vercel build before relying on it — npm workspaces + Vercel's Root
  Directory feature has had rough edges historically; if the override
  above doesn't work, the documented fallback is a root-level
  `vercel.json` with `"installCommand": "npm install"` and Root Directory
  left at the repo root, with `outputDirectory` pointed at
  `apps/web/.next`.
