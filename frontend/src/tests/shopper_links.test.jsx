import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import Checkout from "../pages/shopper/Checkout.jsx";
import Orders from "../pages/shopper/Orders.jsx";
import ShopperRentals from "../pages/shopper/Rentals.jsx";

vi.mock("../context/CartContext.jsx", () => ({
  useCart: () => ({
    cart: { items: [{ id: "i" }], total_items: 1, total_paisa: 1000, currency: "BDT" },
    refresh: () => {},
  }),
}));

const json = (data) => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(data) });
afterEach(() => vi.restoreAllMocks());

describe("Member 3 gaps", () => {
  it("checkout says payment is simulated", () => {
    render(<MemoryRouter><Checkout /></MemoryRouter>);
    expect(screen.getByRole("note")).toHaveTextContent(/simulated payment/i);
  });

  it("an order links to the complaint form with its id", async () => {
    global.fetch = vi.fn(() => json({ items: [{ id: "o1", order_number: "FS-1", status: "delivered", total_paisa: 1000, currency: "BDT", created_at: null, items: [] }] }));
    render(<MemoryRouter><Orders /></MemoryRouter>);
    const link = await screen.findByRole("link", { name: /report a problem/i });
    expect(link).toHaveAttribute("href", "/app/complaints?type=order&id=o1");
  });

  it("a rental request links to the complaint form with its id", async () => {
    global.fetch = vi.fn((url) =>
      json(String(url).includes("requests") ? { items: [{ id: "r1", start_date: "2026-11-01", end_date: "2026-11-02", total_paisa: 100, status: "pending" }] } : { items: [] })
    );
    render(<MemoryRouter><ShopperRentals /></MemoryRouter>);
    const link = await screen.findByRole("link", { name: /report a problem/i });
    expect(link).toHaveAttribute("href", "/app/complaints?type=rental&id=r1");
  });
});