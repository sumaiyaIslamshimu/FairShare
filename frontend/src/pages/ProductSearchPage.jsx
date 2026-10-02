import { useEffect, useState } from 'react';
import ProductCard from '../components/ProductCard';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const CATEGORIES = ['Electronics', 'Fashion', 'Groceries', 'Household'];

function ProductSearchPage({ onSearchChange }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [minimumRating, setMinimumRating] = useState('');
  const [sort, setSort] = useState('Most Relevant');
  const [comparedProducts, setComparedProducts] = useState([]);
  const [savedProducts, setSavedProducts] = useState([]);

  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(async () => {
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.set('q', searchQuery.trim());
      if (minPrice) params.set('min_price', minPrice);
      if (maxPrice) params.set('max_price', maxPrice);
      if (selectedCategories.length) params.set('category', selectedCategories.join(','));
      if (minimumRating) params.set('rating_min', minimumRating);
      if (sort !== 'Most Relevant') params.set('sort', sort);

      setError('');
      if (minPrice && maxPrice && Number(minPrice) > Number(maxPrice)) {
        setProducts([]);
        setLoading(false);
        return;
      }
      setLoading(true);

      try {
        const query = params.toString();
        const response = await fetch(
          `${API_BASE_URL}/products/search${query ? `?${query}` : ''}`,
          { signal: controller.signal },
        );
        if (!response.ok) {
          const detail = await response.json().catch(() => null);
          throw new Error(detail?.detail || 'Could not load products. Please try again.');
        }

        const data = await response.json();
        if (!Array.isArray(data)) throw new Error('The product service returned an invalid response.');
        setProducts(data);
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setError(requestError.message);
          setProducts([]);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [searchQuery, minPrice, maxPrice, selectedCategories, minimumRating, sort]);

  useEffect(() => {
    onSearchChange(searchQuery);
  }, [onSearchChange, searchQuery]);

  function toggleCategory(category) {
    setSelectedCategories((current) => (
      current.includes(category)
        ? current.filter((selected) => selected !== category)
        : [...current, category]
    ));
  }

  function toggleProduct(product, setList) {
    const id = product._id || product.id;
    setList((current) => (
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    ));
  }

  function submitSearch(event) {
    event.preventDefault();
  }

  const priceRangeError = minPrice && maxPrice && Number(minPrice) > Number(maxPrice);

  return (
    <main className="search-page">
      <div className="page-heading">
        <h1>Search &amp; Browse</h1>
        <p>Discover the best deals across all sellers</p>
      </div>

      <form className="product-search" onSubmit={submitSearch}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="10.8" cy="10.8" r="6.8" />
          <path d="m16 16 4.5 4.5" />
        </svg>
        <input
          aria-label="Search product name, brand or category"
          placeholder="Search product name, brand or category..."
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
        />
        <button type="submit">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="10.8" cy="10.8" r="6.8" />
            <path d="m16 16 4.5 4.5" />
          </svg>
          Search
        </button>
      </form>

      {priceRangeError && (
        <p className="filter-error" role="alert">Minimum price cannot be greater than maximum price.</p>
      )}

      <div className="browse-layout">
        <aside className="filters-panel" aria-label="Product filters">
          <section className="filter-section">
            <h2>Price Range</h2>
            <div className="price-inputs">
              <label>
                <span className="visually-hidden">Minimum price</span>
                <input
                  type="number"
                  min="0"
                  placeholder="Min"
                  value={minPrice}
                  onChange={(event) => setMinPrice(event.target.value)}
                />
              </label>
              <span aria-hidden="true">–</span>
              <label>
                <span className="visually-hidden">Maximum price</span>
                <input
                  type="number"
                  min="0"
                  placeholder="Max"
                  value={maxPrice}
                  onChange={(event) => setMaxPrice(event.target.value)}
                />
              </label>
            </div>
          </section>

          <section className="filter-section">
            <div className="filter-heading">
              <h2>Category</h2>
              {selectedCategories.length > 0 && (
                <button className="clear-filters" type="button" onClick={() => setSelectedCategories([])}>
                  Clear
                </button>
              )}
            </div>
            <div className="filter-options">
              {CATEGORIES.map((category) => (
                <label className="filter-option" key={category}>
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(category)}
                    onChange={() => toggleCategory(category)}
                  />
                  <span>{category}</span>
                </label>
              ))}
            </div>
          </section>

          <section className="filter-section rating-filter">
            <h2>Rating</h2>
            <div className="filter-options">
              {[4, 3, 2].map((rating) => (
                <label className="filter-option rating-option" key={rating}>
                  <input
                    type="radio"
                    name="minimum-rating"
                    value={rating}
                    checked={minimumRating === String(rating)}
                    onChange={() => setMinimumRating(String(rating))}
                  />
                  <span className="rating-stars">
                    {'★'.repeat(rating)}{'☆'.repeat(5 - rating)}
                  </span>
                  <span className="rating-up">&amp; up</span>
                </label>
              ))}
              {minimumRating && (
                <button className="clear-filters" type="button" onClick={() => setMinimumRating('')}>
                  Clear rating
                </button>
              )}
            </div>
          </section>
        </aside>

        <section className="results-section" aria-label="Product search results">
          <div className="results-toolbar">
            <p aria-live="polite">
              {loading ? 'Finding products…' : `${products.length} products found`}
            </p>
            <label className="sort-control">
              <span className="visually-hidden">Sort products</span>
              <select value={sort} onChange={(event) => setSort(event.target.value)}>
                <option>Most Relevant</option>
                <option>Price: low to high</option>
                <option>Price: high to low</option>
                <option>Rating</option>
              </select>
            </label>
          </div>

          {error && <p className="request-error" role="alert">{error}</p>}
          {loading && <p className="results-message">Loading products…</p>}
          {!loading && !error && products.length === 0 && (
            <p className="results-message">No products found matching your filters.</p>
          )}
          {!loading && products.length > 0 && (
            <div className="product-grid">
              {products.map((product) => {
                const id = product._id || product.id;
                return (
                  <ProductCard
                    key={id}
                    product={product}
                    isCompared={comparedProducts.includes(id)}
                    isSaved={savedProducts.includes(id)}
                    onCompare={() => toggleProduct(product, setComparedProducts)}
                    onSave={() => toggleProduct(product, setSavedProducts)}
                  />
                );
              })}
            </div>
          )}
          {comparedProducts.length > 0 && (
            <div className="compare-status" role="status">
              {comparedProducts.length} product{comparedProducts.length === 1 ? '' : 's'} selected to compare
              <button type="button" onClick={() => setComparedProducts([])}>Clear</button>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

export default ProductSearchPage;
