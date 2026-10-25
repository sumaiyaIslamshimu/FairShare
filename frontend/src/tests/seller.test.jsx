import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthContext } from "../context/AuthContext.jsx";
import Products from "../pages/seller/Products.jsx";
import BusinessProfile from "../pages/seller/BusinessProfile.jsx";

const json = (data, status = 200) =>
  Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(data) });

function mockApi(routes) {
  global.fetch = vi.fn((url, opts = {}) => {
    const path = String(url).replace(/^.*\/api/, "");
    const key = `${opts.method || "GET"} ${path.split("?")[0]}`;
    const handler = routes[key];
    if (!handler) return json({ error: { code: "NOT_FOUND", message: `no mock for ${key}` } }, 404);
    return typeof handler === "function" ? handler(opts) : json(handler);
  });
}

const wrap = (ui) => (
  <AuthContext.Provider value={{ user: { role: "seller", full_name: "S" }, loading: false }}>
    <MemoryRouter>{ui}</MemoryRouter>
  </AuthContext.Provider>
);

const cats = [{ slug: "groceries-food", name: "Groceries", subcategories: [{ slug: "rice", name: "Rice" }] }];
const product = {
  id: "p1", seller_id: "s1", title: "Miniket Rice", description: "", brand: null, category_slug: "groceries-food",
  subcategory_slug: "rice", price_paisa: 12050, effective_price_paisa: 12050, currency: "BDT", availability: "in_stock",
  images: [], quantity: 5, unit: "g", attributes: {}, source: "fairshare", stock_qty: 0, status: "active", moderation_status: "hidden",
};

afterEach(() => vi.restoreAllMocks());

describe("Seller products", () => {
  it("lists products with stock and admin-hidden state", async () => {
    mockApi({ "GET /seller/products": { items: [product], total: 1, page: 1, page_size: 20 }, "GET /categories": cats });
    render(wrap(<Products />));
    expect(await screen.findByText("Miniket Rice")).toBeInTheDocument();
    expect(screen.getByText("out of stock")).toBeInTheDocument();
    expect(screen.getByText(/hidden by admin/i)).toBeInTheDocument();
  });

  it("creates a product sending price as integer paisa", async () => {
    mockApi({
      "GET /seller/products": { items: [], total: 0, page: 1, page_size: 20 },
      "GET /categories": cats,
      "POST /seller/products": { ...product },
    });
    render(wrap(<Products />));
    fireEvent.click(await screen.findByRole("button", { name: "Add product" }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Rice 5kg" } });
    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "groceries-food" } });
    fireEvent.change(screen.getByLabelText("Subcategory"), { target: { value: "rice" } });
    fireEvent.change(screen.getByLabelText("Price (Taka)"), { target: { value: "199.99" } });
    fireEvent.change(screen.getByLabelText("Stock"), { target: { value: "7" } });
    fireEvent.submit(screen.getByRole("button", { name: "Save product" }).closest("form"));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "POST");
      expect(call).toBeTruthy();
      const body = JSON.parse(call[1].body);
      expect(body.price_paisa).toBe(19999);
      expect(body.stock_qty).toBe(7);
      expect(body.quantity).toBeNull();
      expect(body.seller_id).toBeUndefined();
    });
  });

  it("shows the server's refusal for an unapproved seller", async () => {
    mockApi({
      "GET /seller/products": { items: [], total: 0, page: 1, page_size: 20 },
      "GET /categories": cats,
      "POST /seller/products": () => json({ error: { code: "SELLER_NOT_APPROVED", message: "Your seller account is not approved yet." } }, 403),
    });
    render(wrap(<Products />));
    fireEvent.click(await screen.findByRole("button", { name: "Add product" }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Rice 5kg" } });
    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "groceries-food" } });
    fireEvent.change(screen.getByLabelText("Subcategory"), { target: { value: "rice" } });
    fireEvent.change(screen.getByLabelText("Price (Taka)"), { target: { value: "10" } });
    fireEvent.submit(screen.getByRole("button", { name: "Save product" }).closest("form"));
    expect(await screen.findByText(/not approved yet/i)).toBeInTheDocument();
  });
});

describe("Business profile", () => {
  const profile = { id: "x", user_id: "u", business_name: "Rahim Store", description: "", contact_phone: "", address: "", status: "pending" };

  it("shows status and explains the pending state", async () => {
    mockApi({ "GET /seller/profile": profile });
    render(wrap(<BusinessProfile />));
    expect(await screen.findByDisplayValue("Rahim Store")).toBeInTheDocument();
    expect(screen.getByText(/cannot add products/i)).toBeInTheDocument();
  });

  it("saves changes through the API", async () => {
    mockApi({ "GET /seller/profile": profile, "PUT /seller/profile": { ...profile, contact_phone: "01700000000" } });
    render(wrap(<BusinessProfile />));
    fireEvent.change(await screen.findByLabelText("Contact phone"), { target: { value: "01700000000" } });
    fireEvent.submit(screen.getByRole("button", { name: "Save" }).closest("form"));
    expect(await screen.findByText(/profile saved/i)).toBeInTheDocument();
    const call = global.fetch.mock.calls.find(([, o]) => o?.method === "PUT");
    expect(JSON.parse(call[1].body).contact_phone).toBe("01700000000");
  });
});


describe("Seller product details (attributes)", () => {
  it("shows existing details when editing and sends the edited set", async () => {
    const withAttrs = { ...product, stock_qty: 3, moderation_status: "visible", attributes: { Colour: "Red" } };
    mockApi({
      "GET /seller/products": { items: [withAttrs], total: 1, page: 1, page_size: 20 },
      "GET /categories": cats,
      "PUT /seller/products/p1": withAttrs,
    });
    render(wrap(<Products />));
    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
    expect(screen.getByLabelText("Detail name 1")).toHaveValue("Colour");
    fireEvent.change(screen.getByLabelText("Detail value 1"), { target: { value: "Blue" } });
    fireEvent.click(screen.getByRole("button", { name: "Add detail" }));
    fireEvent.change(screen.getByLabelText("Detail name 2"), { target: { value: "  " } }); // blank name is dropped
    fireEvent.submit(screen.getByRole("button", { name: "Save product" }).closest("form"));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "PUT");
      expect(JSON.parse(call[1].body).attributes).toEqual({ Colour: "Blue" });
    });
  });
});