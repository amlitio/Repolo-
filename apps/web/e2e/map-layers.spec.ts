import { test, expect } from "@playwright/test";

/** Requires a running apps/api at NEXT_PUBLIC_API_URL serving GET /map/layers. */
test.describe("map workspace - load and layer toggle", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/map");
  });

  test("renders the three-pane workspace layout", async ({ page }) => {
    await expect(page.getByRole("complementary", { name: "Layer manager" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "Intelligence panel" })).toBeVisible();
    await expect(page.getByRole("region", { name: "Event timeline" })).toBeVisible();
  });

  test("shows a Mapbox placeholder when no token is configured, or the canvas when it is", async ({
    page,
  }) => {
    const placeholder = page.getByTestId("map-placeholder");
    const canvas = page.getByTestId("mapbox-container");
    await expect(placeholder.or(canvas)).toBeVisible();
  });

  test("loads layers into the layer manager and toggles visibility", async ({ page }) => {
    const layerManager = page.getByRole("complementary", { name: "Layer manager" });
    const firstCheckbox = layerManager.getByRole("checkbox").first();

    await expect(firstCheckbox).toBeVisible({ timeout: 10_000 });
    const wasChecked = await firstCheckbox.isChecked();

    await firstCheckbox.click();
    await expect(firstCheckbox).toBeChecked({ checked: !wasChecked });
  });

  test("expands the event timeline drawer", async ({ page }) => {
    const drawer = page.getByRole("region", { name: "Event timeline" });
    await drawer.getByRole("button", { name: /event timeline/i }).click();
    await expect(drawer.getByText(/loading alerts|no active alerts|active$/i)).toBeVisible();
  });
});
