import { test, expect } from "@playwright/test";

/**
 * Requires a real Clerk test instance configured via NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
 * / CLERK_SECRET_KEY, and a running apps/api for the post-login /auth/session
 * call. Use Clerk's testing tokens (https://clerk.com/docs/testing/playwright)
 * to bypass interactive sign-in in CI.
 */
test.describe("login", () => {
  test("unauthenticated user visiting /map is redirected to sign-in", async ({ page }) => {
    await page.goto("/map");
    await expect(page).toHaveURL(/\/sign-in/);
  });

  test("sign-in page renders the Clerk sign-in form", async ({ page }) => {
    await page.goto("/sign-in");
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
  });

  test("authenticated user can reach /map after sign-in", async ({ page }) => {
    test.skip(
      !process.env.E2E_TEST_USER_EMAIL,
      "Set E2E_TEST_USER_EMAIL/E2E_TEST_USER_PASSWORD (Clerk test user) to run this against a live Clerk instance."
    );

    await page.goto("/sign-in");
    await page.getByLabel(/email/i).fill(process.env.E2E_TEST_USER_EMAIL!);
    await page.getByRole("button", { name: /continue/i }).click();
    await page.getByLabel(/password/i).fill(process.env.E2E_TEST_USER_PASSWORD!);
    await page.getByRole("button", { name: /continue/i }).click();

    await page.waitForURL(/\/map|\/$/);
    await page.goto("/map");
    await expect(page).toHaveURL(/\/map/);
  });
});
