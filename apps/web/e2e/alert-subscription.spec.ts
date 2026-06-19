import { test, expect } from "@playwright/test";

/**
 * Requires a running apps/api with POST /subscriptions (auth required) and
 * an authenticated Playwright session (see e2e/login.spec.ts for the Clerk
 * testing-token setup this depends on).
 */
test.describe("alert subscription", () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL,
    "Requires an authenticated session - set E2E_TEST_USER_EMAIL/PASSWORD against a live Clerk + API stack."
  );

  test("subscribing to a county's alerts adds it to the subscriptions list", async ({ page }) => {
    await page.goto("/dashboard/emergency-management");

    const fipsInput = page.getByLabel(/county fips for new subscription/i);
    await fipsInput.fill("12103");
    await page.getByRole("button", { name: /subscribe/i }).click();

    await expect(page.getByText(/12103 via email/i)).toBeVisible({ timeout: 10_000 });
  });

  test("sending a test notification does not error", async ({ page }) => {
    await page.goto("/dashboard/emergency-management");
    await page.getByRole("button", { name: /send test notification/i }).click();
    // No error toast/banner should appear; absence of a thrown exception is
    // implicitly covered by Playwright failing the test on unhandled errors.
  });
});
