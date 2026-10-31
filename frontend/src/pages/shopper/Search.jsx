import { useEffect, useState } from "react";
import Button from "../../components/Button.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Pagination from "../../components/Pagination.jsx";
import ProductCard from "../../components/shopping/ProductCard.jsx";
import ProductModal from "../../components/shopping/ProductModal.jsx";
import { searchProducts } from "../../api/shopping.js";
import "../../styles/shopping.css";

const EMPTY = { q: "", category: "", subcategory: "", store: "", sort: "price_asc" };

// Playful SVG Spinner Component
const Spinner = ({ size = 20, color = "#888", style }) => (
  <svg
    className="spin-anim"
    width={size} height={size} viewBox="0 0 24 24"
    fill="none" stroke={color} strokeWidth="3"
    strokeLinecap="round" strokeLinejoin="round"
    style={style}
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
);

export default function Search() {
  const [form, setForm] = useState(EMPTY);
  const [applied, setApplied] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(48);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // State for the Chaldal-style product detail modal
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    searchProducts({ ...applied, page, page_size: pageSize })
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [applied, page, pageSize]);

  function onSubmit(e) {
    e.preventDefault();
    setPage(1);
    setApplied(form);
  }

  function handlePageSizeChange(e) {
    setPageSize(Number(e.target.value));
    setPage(1);
  }

  return (
    <>
      <h1>Search &amp; Compare</h1>

      <p className="subtitle">
        Compare prices from online stores with FairShare sellers.
        Store prices are labelled with how recent they are.
      </p>

      <form onSubmit={onSubmit}>
        <div className="search-bar" style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>

          {/* Input wrapper to hold the absolute position spinner */}
          <div style={{ position: "relative", flex: "1", minWidth: "200px" }}>
            <input
              className="input"
              type="search"
              placeholder="Search products or brands"
              aria-label="Search"
              value={form.q}
              onChange={(e) => setForm({ ...form, q: e.target.value })}
              style={{ width: "100%", paddingRight: loading ? "40px" : "15px" }}
            />
            {/* Inline search bar spinner */}
            {loading && (
              <div style={{ position: "absolute", right: "12px", top: "50%", marginTop: "-10px", pointerEvents: "none" }}>
                <Spinner size={20} color="var(--primary, #007bff)" />
              </div>
            )}
          </div>

          <select
            className="input"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            style={{ width: "auto", minWidth: "150px" }}
          >
            <option value="">All Categories</option>
            <option value="electronics">Electronics</option>
            <option value="groceries">Groceries</option>
            <option value="lifestyle">Lifestyle</option>
          </select>

          <Button variant="primary" type="submit">
            Search
          </Button>
        </div>
      </form>

      <ErrorBox error={error} />

      {/* Playful Loading State with side-by-side Spinner */}
      {loading && !data && (
        <div className="fade-in-up" style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "12px", padding: "4rem 0", color: "#666" }}>
          <Spinner size={28} color="var(--primary, #007bff)" />
          <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: "500" }}>Loading...</h2>
        </div>
      )}

      {!loading && data && data.items.length === 0 && (
        <div className="fade-in-up">
          <EmptyState title="No products found.">
            Try a different search or category.
          </EmptyState>
        </div>
      )}

      {/* Renders the grid conditionally and uses a dynamic key to re-trigger the animation on page change */}
      {data && data.items.length > 0 && (
        <div key={`${page}-${applied.q}-${applied.category}`} className="fade-in-up">
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "1rem", alignItems: "center", gap: "0.5rem" }}>
            <label htmlFor="pageSizeSelect" style={{ fontSize: "0.9rem", color: "var(--text-muted, #666)" }}>
              Products per page:
            </label>
            <select
              id="pageSizeSelect"
              className="input"
              value={pageSize}
              onChange={handlePageSizeChange}
              style={{ width: "auto", padding: "0.3rem 0.5rem", minHeight: "unset" }}
            >
              <option value={12}>12</option>
              <option value={24}>24</option>
              <option value={36}>36</option>
              <option value={48}>48</option>
            </select>
          </div>

          <div className="product-grid" style={loading ? { opacity: 0.5, pointerEvents: "none" } : {}}>
            {data.items.map((item) => (
              <div
                key={`${item.source}-${item.id}`}
                onClick={() => setSelectedProduct(item)}
                style={{ cursor: "pointer" }}
              >
                <ProductCard item={item} />
              </div>
            ))}
          </div>

          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onChange={setPage}
          />
        </div>
      )}

      {/* Chaldal-style popup modal component */}
      <ProductModal item={selectedProduct} onClose={() => setSelectedProduct(null)} />
    </>
  );
}