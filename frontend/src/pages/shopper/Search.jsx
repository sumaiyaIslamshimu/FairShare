import { useEffect, useState } from "react";
import Button from "../../components/Button.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Pagination from "../../components/Pagination.jsx";
import ProductCard from "../../components/shopping/ProductCard.jsx";
import ProductModal from "../../components/shopping/ProductModal.jsx";
import { searchProducts } from "../../api/shopping.js";
import "../../styles/shopping.css";

// Changed default sort to relevance
const EMPTY = { q: "", category: "", subcategory: "", store: "", sort: "relevance", fairshareOnly: false };

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

  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    // Build the query parameters based on what was ACTUALLY submitted via the form
    const searchParams = {
      q: applied.q,
      category: applied.category,
      subcategory: applied.subcategory,
      store: applied.store,
      sort: applied.sort,
      page,
      page_size: pageSize,
      ...(applied.fairshareOnly && { source: "fairshare" })
    };

    searchProducts(searchParams)
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
    // Apply the form state (including the checkbox) to trigger the search
    setApplied(form);
  }

  function handlePageSizeChange(e) {
    setPageSize(Number(e.target.value));
    setPage(1);
  }

  // Trigger search instantly when sort option changes
  function handleSortChange(e) {
    const newSort = e.target.value;
    setForm({ ...form, sort: newSort });
    setApplied({ ...applied, sort: newSort });
    setPage(1);
  }

  return (
    <>
      <h1>Search &amp; Compare</h1>

      <p className="subtitle">
        Compare prices from online stores with FairShare sellers.
        Store prices are labelled with how recent they are.
      </p>

      {/* Form wraps both the inputs and the checkbox so they submit together */}
      <form onSubmit={onSubmit} style={{ marginBottom: "1.5rem" }}>
        <div className="search-bar" style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.75rem" }}>

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

        {/* Tick Style Checkbox directly under the search bar */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", paddingLeft: "0.25rem" }}>
          <input
            type="checkbox"
            id="fairshareOnlyToggle"
            checked={form.fairshareOnly}
            onChange={(e) => setForm({ ...form, fairshareOnly: e.target.checked })}
            style={{
              width: "16px",
              height: "16px",
              cursor: "pointer",
              accentColor: "var(--primary, #10b981)"
            }}
          />
          <label
            htmlFor="fairshareOnlyToggle"
            style={{
              fontSize: "0.95rem",
              color: "var(--text, #374151)",
              cursor: "pointer",
              userSelect: "none"
            }}
          >
            Show FairShare Sellers Only
          </label>
        </div>
      </form>

      <ErrorBox error={error} />

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

      {data && data.items.length > 0 && (
        <div key={`${page}-${applied.q}-${applied.category}-${applied.fairshareOnly}`} className="fade-in-up">

          {/* Top Controls: Sort By and Products Per Page */}
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "1rem", alignItems: "center", gap: "1.5rem", flexWrap: "wrap" }}>

            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <label htmlFor="sortSelect" style={{ fontSize: "0.9rem", color: "var(--text-muted, #666)" }}>
                Sort by:
              </label>
              <select
                id="sortSelect"
                className="input"
                value={applied.sort}
                onChange={handleSortChange}
                style={{ width: "auto", padding: "0.3rem 0.5rem", minHeight: "unset" }}
              >
                <option value="relevance">Relevance</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="newest">Recently Updated</option>
              </select>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
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

      <ProductModal item={selectedProduct} onClose={() => setSelectedProduct(null)} />
    </>
  );
}