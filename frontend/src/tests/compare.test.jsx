import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import FreshnessBadge from "../components/shopping/FreshnessBadge.jsx";
import MatchGroupTable from "../components/shopping/MatchGroupTable.jsx";
import ProductCard from "../components/shopping/ProductCard.jsx";
import StoreLink from "../components/shopping/StoreLink.jsx";
import { formatPrice } from "../utils/format.js";

const base = {
  id: "1", source: "external", store: "daraz", store_name: "Daraz", name: "Pran Rice", brand: "Pran",
  price_paisa: 12000, currency: "BDT", availability: "in_stock", quantity: null, unit: null,
  freshness: "fresh", last_updated: null, store_url: "https://shop.test/p/1", group_key: "k", group_size: 2,
};

describe("formatting", () => {
  it("formats paisa and never invents missing values", () => {
    expect(formatPrice(12000, "BDT")).toBe("৳ 120");
    expect(formatPrice(null, "BDT")).toBe("Not available");
    expect(formatPrice(5000, null)).toContain("currency not stated");
  });
});

describe("components", () => {
  it("labels stale prices as possibly outdated", () => {
    render(<FreshnessBadge freshness="stale" source="external" />);
    expect(screen.getByText("Possibly outdated")).toBeInTheDocument();
  });

  it("only renders safe http(s) store links", () => {
    const { rerender } = render(<StoreLink url="https://shop.test/p/1">Open</StoreLink>);
    expect(screen.getByRole("link")).toHaveAttribute("rel", "noopener noreferrer");
    rerender(<StoreLink url="javascript:alert(1)">Open</StoreLink>);
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.getByText("Link not available")).toBeInTheDocument();
  });

  it("external product card links to the store and has no buy button", () => {
    render(<MemoryRouter><ProductCard item={base} /></MemoryRouter>);
    expect(screen.getByText(/View at Daraz/)).toBeInTheDocument();
    expect(screen.queryByText(/add to cart|buy now/i)).toBeNull();
    expect(screen.getByText(/Compare prices \(2\)/)).toBeInTheDocument();
  });

  it("compare table shows Not available for missing size and marks the best price", () => {
    const items = [base, { ...base, id: "2", store: "chaldal", store_name: "Chaldal", price_paisa: 11000 }];
    render(<MatchGroupTable items={items} cheapestId="2" />);
    expect(screen.getAllByText("Not available").length).toBeGreaterThan(0);
    expect(screen.getByText("Best price")).toBeInTheDocument();
  });
});