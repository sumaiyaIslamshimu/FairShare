import { useEffect, useState } from "react";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import CategoryFilter from "../../components/shopping/CategoryFilter.jsx";
import ProductCard from "../../components/shopping/ProductCard.jsx";
import { getCategories, getSources, searchProducts } from "../../api/shopping.js";
import "../../styles/shopping.css";

const PAGE_SIZE = 12;
const STORES = ["daraz", "pickaboo", "chaldal", "shwapno", "agora", "rokomari"];
const STATUS_TONE = { success: "green", partial: "amber", failure: "red", unsupported: "neutral", never_run: "neutral" };
const EMPTY = { q: "", category: "", subcategory: "", store: "", sort: "price_asc" };

export default function Search() {
  const [form, setForm] = useState(EMPTY);
  const [applied, setApplied] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const [categories, setCategories] = useState([]);
  const [sources, setSources] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {});
    getSources().then(setSources).catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    searchProducts({ ...applied, page, page_size: PAGE_SIZE })
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [applied, page]);

  function onSubmit(e) {
    e.preventDefault();
    setPage(1);
    setApplied(form);
  }

  const noExternalData = sources.length > 0 && sources.every((s) => !s.configured || ["never_run", "unsupported", "failure"].includes(s.status));

  return (
    <>
      <h1>Search &amp; Compare</h1>
      <p className="subtitle">Compare prices from online stores with FairShare sellers. Store prices are labelled with how recent they are.</p>

      {sources.length > 0 && (
        <div className="status-strip">
          <small>Store data:</small>
          {sources.map((s) => (
            <Badge key={s.store} tone={s.configured ? STATUS_TONE[s.status] : "neutral"}>
              {s.store_name}: {s.configured ? s.status.replace("_", " ") : "not set up"}
            </Badge>
          ))}
        </div>
      )}
      {noExternalData && (
        <div className="info-box">
          Prices from external stores are not available yet. They appear after an administrator refreshes store data. FairShare listings are shown below.
        </div>
      )}

      <form onSubmit={onSubmit}>
        <div className="search-bar">
          <input className="input" type="search" placeholder="Search products or brands" aria-label="Search"
            value={form.q} onChange={(e) => setForm({ ...form, q: e.target.value })} />
          <Button variant="primary" type="submit">Search</Button>
        </div>
        <div className="filters">
          <CategoryFilter categories={categories} category={form.category} subcategory={form.subcategory}
            onChange={(c) => setForm({ ...form, ...c })} />
          <select className="input" aria-label="Store" value={form.store} onChange={(e) => setForm({ ...form, store: e.target.value })}>
            <option value="">All stores</option>
            <option value="fairshare">FairShare</option>
            {STORES.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
          </select>
          <select className="input" aria-label="Sort" value={form.sort} onChange={(e) => setForm({ ...form, sort: e.target.value })}>
            <option value="price_asc">Price: low to high</option>
            <option value="price_desc">Price: high to low</option>
          </select>
        </div>
      </form>

      <ErrorBox error={error} />
      {loading && <Loading />}
      {!loading && data && data.items.length === 0 && (
        <EmptyState title="No products found.">Try a different search or remove a filter.</EmptyState>
      )}
      {!loading && data && data.items.length > 0 && (
        <>
          <div className="product-grid">
            {data.items.map((item) => <ProductCard key={`${item.source}-${item.id}`} item={item} />)}
          </div>
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onChange={setPage} />
        </>
      )}
    </>
  );
}