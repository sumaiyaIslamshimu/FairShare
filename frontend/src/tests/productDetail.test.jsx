import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import ProductCard from "../components/shopping/ProductCard.jsx";
import ProductDetail from "../pages/shopper/ProductDetail.jsx";

const add = vi.fn(() => Promise.resolve());
vi.mock("../context/CartContext.jsx", () => ({ useCart: () => ({ add }) }));

const json = (data) => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(data) });
afterEach(() => { vi.restoreAllMocks(); add.mockClear(); });

const product = {
  id: "p1", seller_id: "s1", seller_name: "Rahim Store", title: "Rice 5 kg", description: "Good rice", brand: "Aarong",
  price_paisa: 100000, effective_price_paisa: 90000, discount_percent: 10, currency: "BDT", availability: "in_stock",
  images: [], quantity: 5000, unit: "g", attributes: { origin: "Dinajpur" }, source: "fairshare",
};
const reviewsPage = (items) => ({ items, total: items.length, page: 1, page_size: 10, average: items.length ? 4 : null, count: items.length });

function mount(reviewItems, prod = product) {
  global.fetch = vi.fn((url) => json(String(url).includes("/reviews") ? reviewsPage(reviewItems) : prod));
  return render(
    <MemoryRouter initialEntries={["/app/product/p1"]}>
      <Routes><Route path="/app/product/:id" element={<ProductDetail />} /></Routes>
    </MemoryRouter>
  );
}

describe("Product detail", () => {
  it("shows the product, its details and the public reviews", async () => {
    mount([{ id: "r1", product_id: "p1", rating: 4, comment: "Very fresh", reviewer_name: "Karim", created_at: null }]);
    expect(await screen.findByRole("heading", { name: "Rice 5 kg" })).toBeInTheDocument();
    expect(screen.getByText(/Dinajpur/)).toBeInTheDocument();
    expect(await screen.findByText("Very fresh")).toBeInTheDocument();
    expect(screen.getByText("Karim")).toBeInTheDocument();
    expect(screen.getByText(/1 review$/)).toBeInTheDocument();
  });

  it("says so when there are no reviews", async () => {
    mount([]);
    expect(await screen.findByText(/No reviews yet/i)).toBeInTheDocument();
  });

  it("adds the product to the cart", async () => {
    mount([]);
    fireEvent.click(await screen.findByRole("button", { name: /add to cart/i }));
    expect(add).toHaveBeenCalledWith("p1", 1);
    expect(await screen.findByRole("status")).toHaveTextContent(/added/i);
  });

  it("disables adding when the product is out of stock", async () => {
    mount([], { ...product, availability: "out_of_stock" });
    expect(await screen.findByRole("button", { name: /add to cart/i })).toBeDisabled();
  });

  it("a FairShare product card links to its page, an external one does not", () => {
    const base = { name: "Rice", store_name: "X", availability: "in_stock", price_paisa: 100, currency: "BDT" };
    const { rerender } = render(<MemoryRouter><ProductCard item={{ ...base, id: "p1", source: "fairshare" }} /></MemoryRouter>);
    expect(screen.getByRole("link", { name: "Rice" })).toHaveAttribute("href", "/app/product/p1");
    rerender(<MemoryRouter><ProductCard item={{ ...base, id: "e1", source: "external", store_url: "https://x.test" }} /></MemoryRouter>);
    expect(screen.queryByRole("link", { name: "Rice" })).toBeNull();
  });
});