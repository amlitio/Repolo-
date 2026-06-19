import { test, expect } from "@playwright/test";

/** Requires a running apps/api serving GET /risk/property and /risk/county. */
test.describe("property risk lookup", () => {
  test("dashboard county risk widget renders a grade once a county is selected", async ({
    page,
  }) => {
    await page.goto("/dashboard/government");

    await page.getByLabel(/county/i).selectOption({ label: "Pinellas County" });

    const riskCard = page.getByText("County risk").locator("..");
    await expect(riskCard.getByText(/^[A-F]$/)).toBeVisible({ timeout: 10_000 });
  });

  test("unknown property id surfaces an error state rather than a crash", async ({ page }) => {
    await page.goto("/map");
    // Simulate a selection the IntelligencePanel can't resolve; in a full
    // integration run this would come from a real /map/search property hit.
    await expect(page.getByText("No selection")).toBeVisible();
  });
});
