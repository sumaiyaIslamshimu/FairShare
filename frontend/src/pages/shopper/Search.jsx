
import { useEffect, useState } from "react";
import Button from "../../components/Button.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import ProductCard from "../../components/shopping/ProductCard.jsx";
import { searchProducts } from "../../api/shopping.js";
import "../../styles/shopping.css";

const PAGE_SIZE = 12;
const STORES = ["daraz", "pickaboo", "chaldal", "shwapno", "agora", "rokomari"];
const EMPTY = { q: "", category: "", subcategory: "", store: "", sort: "price_asc" };

export default function Search() {
  const [form, setForm] = useState(EMPTY);
  const [applied, setApplied] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  return (
    <>
      <h1>Search &amp; Compare</h1>

      <p className="subtitle">
        Compare prices from online stores with FairShare sellers.
        Store prices are labelled with how recent they are.
      </p>

      <form onSubmit={onSubmit}>
        <div className="search-bar">
          <input
            className="input"
            type="search"
            placeholder="Search products or brands"
            aria-label="Search"
            value={form.q}
            onChange={(e) => setForm({ ...form, q: e.target.value })}
          />

          <Button variant="primary" type="submit">
            Search
          </Button>
        </div>
      </form>

      <ErrorBox error={error} />

      {loading && <Loading />}

      {!loading && data && data.items.length === 0 && (
        <EmptyState title="No products found.">
          Try a different search.
        </EmptyState>
      )}

      {!loading && data && data.items.length > 0 && (
        <>
          <div className="product-grid">
            {data.items.map((item) => (
              <ProductCard
                key={`${item.source}-${item.id}`}
                item={item}
              />
            ))}
          </div>

          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onChange={setPage}
          />
        </>
      )}
    </>
  );
}