import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiClientError } from "@/lib/api/client";

describe("apiFetch", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.test.firip.local";
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.unstubAllGlobals();
  });

  it("returns the parsed body directly on success (no envelope unwrap)", async () => {
    const payload = { id: "abc", name: "Pinellas" };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), { status: 200 })
    );

    const result = await apiFetch<typeof payload>("/water/summary");

    expect(result).toEqual(payload);
  });

  it("throws ApiClientError parsed from the ApiErrorResponse envelope on failure", async () => {
    const errorBody = {
      success: false,
      error: { code: "NOT_FOUND", message: "Property not found", details: ["property_id missing"] },
    };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(errorBody), { status: 404 })
    );

    await expect(apiFetch("/risk/property")).rejects.toMatchObject({
      code: "NOT_FOUND",
      message: "Property not found",
      status: 404,
      details: ["property_id missing"],
    });
  });

  it("throws an ApiClientError instance, not a generic Error, on failure", async () => {
    const errorBody = {
      success: false,
      error: { code: "VALIDATION_ERROR", message: "Invalid bbox", details: [] },
    };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(errorBody), { status: 422 })
    );

    let caught: unknown;
    try {
      await apiFetch("/map/features/query");
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(ApiClientError);
    expect((caught as ApiClientError).code).toBe("VALIDATION_ERROR");
  });

  it("falls back to UNKNOWN_ERROR when a non-2xx response doesn't match the envelope shape", async () => {
    global.fetch = vi.fn().mockResolvedValue(new Response("Internal Server Error", { status: 500 }));

    await expect(apiFetch("/health")).rejects.toMatchObject({
      code: "UNKNOWN_ERROR",
      status: 500,
    });
  });

  it("wraps network failures (fetch throwing) as a NETWORK_ERROR ApiClientError", async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(apiFetch("/health")).rejects.toMatchObject({
      code: "NETWORK_ERROR",
      status: 0,
    });
  });

  it("serializes query params onto the URL and drops empty/undefined values", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({}), { status: 200 }));
    global.fetch = fetchMock;

    await apiFetch("/water/stations", {
      query: { county_fips: "12103", source_id: undefined, page: 2, q: "" },
    });

    const firstCall = fetchMock.mock.calls[0];
    if (!firstCall) throw new Error("expected fetch to have been called");
    const calledUrl = new URL(firstCall[0] as string);
    expect(calledUrl.searchParams.get("county_fips")).toBe("12103");
    expect(calledUrl.searchParams.has("source_id")).toBe(false);
    expect(calledUrl.searchParams.get("page")).toBe("2");
    expect(calledUrl.searchParams.has("q")).toBe(false);
  });
});
