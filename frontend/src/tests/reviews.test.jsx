import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthContext } from "../context/AuthContext.jsx";
import MyReviews from "../pages/shopper/MyReviews.jsx";
import AdminReviews from "../pages/admin/Reviews.jsx";
import Orders from "../pages/shopper/Orders.jsx";
import { NAV } from "../navConfig.js";

const json = (data, status = 200) => Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(data) });
function mockApi(routes) {
  global.fetch = vi.fn((url, opts = {}) => {
    const key = `${opts.method || "GET"} ${String(url).replace(/^.*\/api/, "").split("?")[0]}`;
    const h = routes[key];
    if (!h) return json({ error: { code: "NOT_FOUND", message: `no mock for ${key}` } }, 404);
    return typeof h === "function" ? h(opts) : json(h);
  });
}
const wrap = (ui, path = "/") => (
  <AuthContext.Provider value={{ user: { role: "user" }, loading: false }}>
    <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>
  </AuthContext.Provider>
);
afterEach(() => vi.restoreAllMocks());

const mine = { id: "r1", product_id: "p", rating: 4, comment: "Nice", reviewer_name: "Test", created_at: null, order_item_id: "i1", product_title: "Rice", status: "visible" };

describe("reviews", () => {
  it("is in every role's navigation", () => {
    expect(NAV.user.map((i) => i.to)).toContain("/app/reviews");
    expect(NAV.seller.map((i) => i.to)).toContain("/seller/reviews");
    expect(NAV.admin.map((i) => i.to)).toContain("/admin/reviews");
  });

  it("delivered order items link to the review form, others do not", async () => {
    mockApi({ "GET /orders": { items: [{ id: "o1", order_number: "O-1", status: "delivered", total_paisa: 100, currency: "BDT", created_at: null,
      items: [{ id: "i1", title_snapshot: "Rice", quantity: 1, line_total_paisa: 100, item_status: "delivered" },
              { id: "i2", title_snapshot: "Oil", quantity: 1, line_total_paisa: 100, item_status: "shipped" }] }] } });
    render(wrap(<Orders />));
    const links = await screen.findAllByRole("link", { name: "Write a review" });
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute("href", "/app/reviews?item=i1");
  });

  it("posts a review for the item in the URL", async () => {
    mockApi({ "GET /reviews/mine": { items: [], total: 0, page: 1, page_size: 20 }, "POST /reviews": mine });
    render(wrap(<MyReviews />, "/app/reviews?item=i1"));
    fireEvent.change(await screen.findByLabelText("Rating"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText(/Your comment/), { target: { value: "ok" } });
    fireEvent.submit(screen.getByRole("button", { name: "Post review" }).closest("form"));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "POST");
      expect(JSON.parse(call[1].body)).toEqual({ order_item_id: "i1", rating: 3, comment: "ok" });
    });
  });

  it("shows the server's 'not delivered' refusal", async () => {
    mockApi({
      "GET /reviews/mine": { items: [], total: 0, page: 1, page_size: 20 },
      "POST /reviews": () => json({ error: { code: "NOT_DELIVERED", message: "You can review an item only after it has been delivered." } }, 409),
    });
    render(wrap(<MyReviews />, "/app/reviews?item=i1"));
    fireEvent.submit((await screen.findByRole("button", { name: "Post review" })).closest("form"));
    expect(await screen.findByText(/only after it has been delivered/i)).toBeInTheDocument();
  });

  it("tells the shopper when an administrator hid their review", async () => {
    mockApi({ "GET /reviews/mine": { items: [{ ...mine, status: "hidden" }], total: 1, page: 1, page_size: 20 } });
    render(wrap(<MyReviews />));
    expect(await screen.findByText(/hidden by an administrator/i)).toBeInTheDocument();
  });

  it("admin can hide a review", async () => {
    mockApi({
      "GET /admin/reviews": { items: [{ ...mine, seller_id: "s", reviewer_email: "a@b.c" }], total: 1, page: 1, page_size: 20 },
      "PATCH /admin/reviews/r1": { ...mine, status: "hidden", seller_id: "s", reviewer_email: "a@b.c" },
    });
    render(wrap(<AdminReviews />));
    fireEvent.click(await screen.findByRole("button", { name: "Hide" }));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "PATCH");
      expect(JSON.parse(call[1].body)).toEqual({ status: "hidden" });
    });
  });
});