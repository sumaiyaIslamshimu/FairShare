import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthContext } from "../context/AuthContext.jsx";
import MyReturns from "../pages/shopper/MyReturns.jsx";
import SellerReturns from "../pages/seller/Returns.jsx";
import AdminReturns from "../pages/admin/Returns.jsx";
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

const row = {
  id: "t1", order_id: "o", order_item_id: "i1", product_title: "Rice", quantity: 2, refund_paisa: 24100, currency: "BDT",
  refund_mode: "simulated", reason: "damaged", details: "Torn bag", status: "requested", seller_note: null, created_at: null,
  shopper_name: "Rahim", shopper_email: "r@x.com", seller_id: "s",
};
const page = (items) => ({ items, total: items.length, page: 1, page_size: 20 });

describe("returns", () => {
  it("is in every role's navigation", () => {
    expect(NAV.user.map((i) => i.to)).toContain("/app/returns");
    expect(NAV.seller.map((i) => i.to)).toContain("/seller/returns");
    expect(NAV.admin.map((i) => i.to)).toContain("/admin/returns");
  });

  it("delivered order items link to the return form", async () => {
    mockApi({ "GET /orders": { items: [{ id: "o1", order_number: "O-1", status: "delivered", total_paisa: 100, currency: "BDT", created_at: null,
      items: [{ id: "i1", title_snapshot: "Rice", quantity: 1, line_total_paisa: 100, item_status: "delivered" }] }] } });
    render(wrap(<Orders />));
    expect(await screen.findByRole("link", { name: "Return this item" })).toHaveAttribute("href", "/app/returns?item=i1");
  });

  it("sends a return request for the item in the URL", async () => {
    mockApi({ "GET /returns/mine": page([]), "POST /returns": row });
    render(wrap(<MyReturns />, "/app/returns?item=i1"));
    fireEvent.change(await screen.findByLabelText("Reason"), { target: { value: "wrong_item" } });
    fireEvent.submit(screen.getByRole("button", { name: "Send return request" }).closest("form"));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "POST");
      expect(JSON.parse(call[1].body)).toEqual({ order_item_id: "i1", reason: "wrong_item", details: "" });
    });
  });

  it("shows the server's 'not delivered' refusal", async () => {
    mockApi({
      "GET /returns/mine": page([]),
      "POST /returns": () => json({ error: { code: "NOT_DELIVERED", message: "You can return an item only after it has been delivered." } }, 409),
    });
    render(wrap(<MyReturns />, "/app/returns?item=i1"));
    fireEvent.submit((await screen.findByRole("button", { name: "Send return request" })).closest("form"));
    expect(await screen.findByText(/only after it has been delivered/i)).toBeInTheDocument();
  });

  it("shopper sees the seller's reason and the simulated refund; can cancel only while requested", async () => {
    mockApi({ "GET /returns/mine": page([{ ...row, status: "rejected", seller_note: "Opened and used" }, { ...row, id: "t2" }]) });
    render(wrap(<MyReturns />));
    expect(await screen.findByText(/Opened and used/)).toBeInTheDocument();
    expect(screen.getAllByText(/simulated/i).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Cancel request" })).toHaveLength(1);
  });

  it("seller approves, and must give a reason to reject", async () => {
    mockApi({ "GET /seller/returns": page([row]), "PATCH /seller/returns/t1": { ...row, status: "approved" } });
    render(wrap(<SellerReturns />));
    fireEvent.click(await screen.findByRole("button", { name: "Reject" }));
    const dialog = await screen.findByRole("dialog");
    const confirm = dialog.querySelector("button.btn-primary");
    expect(confirm).toBeDisabled();
    fireEvent.change(dialog.querySelector("textarea"), { target: { value: "Used item" } });
    expect(confirm).not.toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "PATCH");
      expect(JSON.parse(call[1].body)).toEqual({ action: "approve", note: "" });
    });
  });

  it("approved requests offer restock; admin page uses the admin API", async () => {
    mockApi({ "GET /admin/returns": page([{ ...row, status: "approved" }]), "PATCH /admin/returns/t1": { ...row, status: "completed" } });
    render(wrap(<AdminReturns />));
    fireEvent.click(await screen.findByRole("button", { name: /Mark received/ }));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "PATCH");
      expect(call[0]).toContain("/admin/returns/t1");
      expect(JSON.parse(call[1].body).action).toBe("complete");
    });
  });
});