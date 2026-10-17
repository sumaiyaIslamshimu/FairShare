import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, request, tokenStore } from "../api/client.js";

const jsonResponse = (status, body) => ({ ok: status < 400, status, json: async () => body });

describe("api client", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => vi.restoreAllMocks());

  it("returns parsed JSON and sends the bearer token", async () => {
    tokenStore.set("abc");
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(200, { ok: true }));
    const data = await request("/auth/me");
    expect(data).toEqual({ ok: true });
    expect(spy.mock.calls[0][1].headers.Authorization).toBe("Bearer abc");
  });

  it("throws ApiError using the standard error format", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(409, { error: { code: "EMAIL_EXISTS", message: "An account with this email already exists." } })
    );
    await expect(request("/auth/register", { method: "POST", body: {}, auth: false })).rejects.toMatchObject({
      name: "ApiError", status: 409, code: "EMAIL_EXISTS",
    });
  });

  it("clears the token on 401", async () => {
    tokenStore.set("old");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(401, { error: { code: "INVALID_TOKEN", message: "x" } }));
    await expect(request("/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect(tokenStore.get()).toBeNull();
  });

  it("reports a friendly message when the server is unreachable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("fail"));
    await expect(request("/health")).rejects.toMatchObject({ code: "NETWORK_ERROR" });
  });
});