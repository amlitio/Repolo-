import type { ApiErrorResponse } from "@firip/shared";

/**
 * Thrown for every non-2xx response from the FastAPI backend. The backend's
 * single global exception handler always returns ApiErrorResponse on
 * failure (see packages/shared/src/types/api.ts), so we parse that envelope
 * here and re-throw a flat, typed error that call sites and React Query
 * error boundaries can branch on without re-parsing JSON.
 */
export class ApiClientError extends Error {
  readonly code: string;
  readonly details: unknown[];
  readonly status: number;

  constructor(params: { code: string; message: string; details: unknown[]; status: number }) {
    super(params.message);
    this.name = "ApiClientError";
    this.code = params.code;
    this.details = params.details;
    this.status = params.status;
  }
}

function getApiBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    // Fall back to localhost in dev rather than throwing at import time -
    // this file is imported by client components that may render before
    // env validation runs, and we never want a missing env var to crash
    // `next build` (no network calls happen at build time anyway).
    return "http://localhost:8000";
  }
  return url.replace(/\/+$/, "");
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    candidate.success === false &&
    typeof candidate.error === "object" &&
    candidate.error !== null &&
    typeof (candidate.error as Record<string, unknown>).code === "string" &&
    typeof (candidate.error as Record<string, unknown>).message === "string"
  );
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  signal?: AbortSignal;
  /** Forwarded to fetch's credentials option; defaults to "include" so the Clerk session cookie rides along. */
  credentials?: RequestCredentials;
  /** Extra headers, e.g. an Authorization bearer token obtained from Clerk on the server. */
  headers?: Record<string, string>;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const base = getApiBaseUrl();
  const url = new URL(path.startsWith("/") ? path.slice(1) : path, `${base}/`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

/**
 * Typed fetch wrapper used by every function in lib/api/endpoints.ts.
 * Resolves with the parsed success body (T) directly - success responses
 * from apps/api are the bare resource, never wrapped - and throws
 * ApiClientError for any non-2xx response.
 */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, signal, credentials = "include", headers } = options;

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      credentials,
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (cause) {
    throw new ApiClientError({
      code: "NETWORK_ERROR",
      message: cause instanceof Error ? cause.message : "Network request failed",
      details: [],
      status: 0,
    });
  }

  // 204 No Content / empty bodies (e.g. some DELETE/POST acks).
  const text = await response.text();
  const data: unknown = text.length > 0 ? safeJsonParse(text) : undefined;

  if (!response.ok) {
    if (isApiErrorResponse(data)) {
      throw new ApiClientError({
        code: data.error.code,
        message: data.error.message,
        details: data.error.details,
        status: response.status,
      });
    }
    throw new ApiClientError({
      code: "UNKNOWN_ERROR",
      message: response.statusText || `Request failed with status ${response.status}`,
      details: [],
      status: response.status,
    });
  }

  return data as T;
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}
