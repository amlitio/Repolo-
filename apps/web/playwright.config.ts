import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for FIRIP web e2e specs. These specs are written to run
 * against a real dev server (apps/web) with a real apps/api backend - they
 * are NOT executed as part of `npm run build`/`lint`/`typecheck`/`test` in
 * this sandbox (no live backend, no Mapbox/Clerk network access). Run them
 * locally or in CI once both services are up - see README.md "Running
 * Playwright e2e" section.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.PLAYWRIGHT_SKIP_WEBSERVER
    ? undefined
    : {
        command: "npm run dev",
        url: "http://localhost:3000",
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
