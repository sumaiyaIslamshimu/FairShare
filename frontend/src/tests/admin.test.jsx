import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthContext } from "../context/AuthContext.jsx";
import { NAV } from "../navConfig.js";
import AppRoutes from "../routes.jsx";
import Verification from "../pages/shared/Verification.jsx";
import SellerVerification from "../pages/admin/SellerVerification.jsx";
import Categories from "../pages/admin/Categories.jsx";
import { request } from "../api/client.js";
import { submitVerification } from "../api/verification.js";

const json = (data, status = 200) =>
  Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(data), blob: () => Promise.resolve(new Blob(["x"])) });

function mockApi(routes) {
  global.fetch = vi.fn((url, opts = {}) => {
    const path = String(url).replace(/^.*\/api/, "");
    const key = `${opts.method || "GET"} ${path.split("?")[0]}`;
    const handler = routes[key];
    if (!handler) return json({ error: { code: "NOT_FOUND", message: `no mock for ${key}` } }, 404);
    return typeof handler === "function" ? handler(opts) : json(handler);
  });
}

const wrap = (ui, user = { role: "admin", full_name: "Admin" }) => (
  <AuthContext.Provider value={{ user, loading: false, refreshUser: vi.fn() }}>
    <MemoryRouter>{ui}</MemoryRouter>
  </AuthContext.Provider>
);

afterEach(() => vi.restoreAllMocks());

describe("navigation", () => {
  it("has an admin link for every Member 4 admin page and no dead routes", () => {
    const admin = NAV.admin.map((i) => i.to);
    for (const p of ["/admin/users", "/admin/verification", "/admin/listings", "/admin/categories", "/admin/complaints", "/admin/scraping", "/admin/audit"]) {
      expect(admin).toContain(p);
    }
    expect(NAV.user.map((i) => i.to)).toContain("/app/verification");
    expect(NAV.seller.map((i) => i.to)).toContain("/seller/complaints");
  });

  it("every sidebar item points at a registered route", () => {
    const html = AppRoutes.toString();
    for (const items of Object.values(NAV)) {
      for (const { to } of items) {
        const leaf = to.split("/").pop();
        if (["app", "seller", "admin"].includes(leaf)) continue;
        expect(html.includes(`path="${leaf}"`) || html.includes(`path: "${leaf}"`)).toBe(true);
      }
    }
  });
});

describe("api client", () => {
  it("sends FormData without forcing a JSON content type", async () => {
    mockApi({ "POST /verification/submit": { status: "pending" } });
    await submitVerification("1234567890", new File(["%PDF-"], "id.pdf", { type: "application/pdf" }));
    const [, opts] = global.fetch.mock.calls[0];
    expect(opts.body instanceof FormData).toBe(true);
    expect(opts.headers["Content-Type"]).toBeUndefined();
    expect(opts.body.get("nid_number")).toBe("1234567890");
  });

  it("still sends JSON for normal calls", async () => {
    mockApi({ "POST /x": { ok: true } });
    await request("/x", { method: "POST", body: { a: 1 } });
    const [, opts] = global.fetch.mock.calls[0];
    expect(opts.headers["Content-Type"]).toBe("application/json");
    expect(opts.body).toBe('{"a":1}');
  });
});

describe("Verification page", () => {
  it("shows the manual-review notice and the form when nothing was submitted", async () => {
    mockApi({ "GET /verification/status": { status: "none", manual_review: true } });
    render(wrap(<Verification />, { role: "user", full_name: "A" }));
    expect(await screen.findByText(/manually/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/NID number/i)).toBeInTheDocument();
  });

  it("hides the form while pending and never shows an NID", async () => {
    mockApi({ "GET /verification/status": { status: "pending", submitted_at: "2026-10-01T00:00:00+00:00", manual_review: true } });
    render(wrap(<Verification />, { role: "user", full_name: "A" }));
    expect(await screen.findByText(/waiting for review/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/NID number/i)).toBeNull();
  });

  it("shows the rejection reason and lets the person resubmit", async () => {
    mockApi({ "GET /verification/status": { status: "rejected", note: "Photo is blurry" } });
    render(wrap(<Verification />, { role: "user", full_name: "A" }));
    expect(await screen.findByText(/Photo is blurry/)).toBeInTheDocument();
    expect(screen.getByLabelText(/NID number/i)).toBeInTheDocument();
  });

  it("refuses a file over 5 MB before uploading", async () => {
    mockApi({ "GET /verification/status": { status: "none" } });
    render(wrap(<Verification />, { role: "user", full_name: "A" }));
    fireEvent.change(await screen.findByLabelText(/NID number/i), { target: { value: "1234567890" } });
    const big = new File(["x"], "big.pdf", { type: "application/pdf" });
    Object.defineProperty(big, "size", { value: 6 * 1024 * 1024 });
    fireEvent.change(screen.getByLabelText(/Document photo/i), { target: { files: [big] } });
    fireEvent.submit(screen.getByRole("button", { name: /submit for review/i }).closest("form"));
    expect(await screen.findByText(/too large/i)).toBeInTheDocument();
    expect(global.fetch.mock.calls.some(([, o]) => o?.method === "POST")).toBe(false);
  });
});

describe("Admin verification queue", () => {
  const rec = { id: "r1", user_id: "u1", user_name: "Rahim", user_email: "r@x.com", user_role: "seller", nid_masked: "*********0123", has_document: true, status: "pending", submitted_at: null };

  it("shows only the masked NID and requires a reason to reject", async () => {
    mockApi({
      "GET /admin/verifications": { items: [rec], total: 1, page: 1, page_size: 50 },
      "GET /admin/sellers": { items: [], total: 0, page: 1, page_size: 50 },
    });
    render(wrap(<SellerVerification />));
    expect(await screen.findByText("*********0123")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Reject" }));
    const dialog = await screen.findByRole("dialog");
    const confirm = dialog.querySelector("button.btn-primary");
    expect(confirm).toBeDisabled();
    fireEvent.change(dialog.querySelector("textarea"), { target: { value: "Blurry" } });
    expect(confirm).not.toBeDisabled();
  });

  it("approves through the API", async () => {
    mockApi({
      "GET /admin/verifications": { items: [rec], total: 1, page: 1, page_size: 50 },
      "GET /admin/sellers": { items: [], total: 0, page: 1, page_size: 50 },
      "PATCH /admin/verifications/r1": { ...rec, status: "approved" },
    });
    render(wrap(<SellerVerification />));
    fireEvent.click(await screen.findByRole("button", { name: "Approve" }));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "PATCH");
      expect(call).toBeTruthy();
      expect(JSON.parse(call[1].body)).toEqual({ decision: "approve" });
    });
  });
});

describe("Admin categories", () => {
  it("shows the server's 'in use' refusal instead of failing silently", async () => {
    const tree = [{ slug: "groceries-food", name: "Groceries", is_active: true, order: 0, in_use: 2, subcategories: [] }];
    mockApi({
      "GET /admin/categories": tree,
      "PUT /admin/categories/groceries-food": () => json({ error: { code: "CATEGORY_IN_USE", message: "Seller listings still use this category." } }, 409),
    });
    render(wrap(<Categories />));
    fireEvent.click(await screen.findByRole("button", { name: "Deactivate" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/still use this category/i);
  });
});