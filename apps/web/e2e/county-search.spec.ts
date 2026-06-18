import { test, expect } from "@playwright/test";

/** Requires a running apps/api serving GET /map/search?q=. */
test.describe("county search", () => {
  test("searching for a county surfaces it in the results list and selecting it loads risk in the intelligence panel", async ({
    page,
  }) => {
    await page.goto("/map");

    const searchInput = page.getByPlaceholderText(/search county, city, or property/i);
    await searchInput.fill("Pinellas");

    const resultButton = page.getByRole("button", { name: /pinellas/i });
    await expect(resultButton).toBeVisible({ timeout: 10_000 });
    await resultButton.click();

    const intelligencePanel = page.getByRole("complementary", { name: "Intelligence panel" });
    await expect(intelligencePanel.getByText(/pinellas/i)).toBeVisible({ timeout: 10_000 });
  });

  test("shows a no-matches message for a nonsense query", async ({ page }) => {
    await page.goto("/map");
    const searchInput = page.getByPlaceholderText(/search county, city, or property/i);
    await searchInput.fill("zzzznonexistentplacezzzz");

    await expect(page.getByText(/no matches for/i)).toBeVisible({ timeout: 10_000 });
  });
});
