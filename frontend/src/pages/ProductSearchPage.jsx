import TrackProductForm from "../components/TrackProductForm";
import { useState, useEffect } from "react";
import SuggestedForYou from "../components/SuggestedForYou";
import VerifiedBadge from "../components/VerifiedBadge";
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

                  <div className="flex items-center gap-3">
                    <button className="text-gray-400 hover:text-gray-600">
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M4 6h16M4 12h16M4 18h16"
                        />
                      </svg>
                    </button>

                    <select
                      value={sort}
                      onChange={(e) => setSort(e.target.value)}
                      className="py-1.5 pl-3 pr-8 border border-gray-200 rounded text-sm text-gray-700 outline-none hover:bg-gray-50 bg-white"
                    >
                      <option value="Most Relevant">
                        Most Relevant
                      </option>

                      <option value="Price: low to high">
                        Price: Low to High
                      </option>

                      <option value="Price: high to low">
                        Price: High to Low
                      </option>
                    </select>
                  </div>
                </div>

                {/* Error */}
                {error && (
                  <div className="p-4 mb-4 bg-red-50 text-red-700 rounded text-sm border border-red-100">
                    Error: {error}
                  </div>
                )}

                {/* Loading */}
                {loading && (
                  <div className="py-12 text-center text-gray-500 text-sm">
                    Loading products...
                  </div>
                )}

                {/* Empty */}
                {!loading && products.length === 0 && !error && (
                  <div className="py-12 text-center text-gray-500 text-sm border border-dashed border-gray-300 rounded-xl bg-white">
                    No products found.
                  </div>
                )}

                {/* Product Cards */}
                {!loading && products.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {products.map((product, index) => (
                      <div
                        key={product.id || index}
                        className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition"
                      >
                        {/* Product Image Placeholder */}
                        <div
                          className={`h-48 relative flex items-center justify-center ${getCardColor(
                            index
                          )}`}
                        >
                          <span className="absolute top-3 left-3 bg-[#E53935] text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                            -20%
                          </span>

                          <button className="absolute top-3 right-3 bg-white/90 p-1.5 rounded-full text-gray-500 hover:text-gray-900 shadow-sm">
                            <svg
                              className="w-3.5 h-3.5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                              />
                            </svg>
                          </button>

                          <svg
                            className="w-16 h-16 text-black/20"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                            />
                          </svg>
                        </div>

                        <div className="p-5">
                          <p className="text-[11px] text-gray-500 mb-1">
                            {product.brand} · {product.category}
                          </p>

                          <h3 className="font-bold text-gray-900 text-sm mb-2 line-clamp-1">
                            {product.name}
                          </h3>

                          <div className="flex items-end gap-2 mb-2">
                            <span className="text-lg font-bold text-gray-900">
                              ৳{product.price}
                            </span>

                            <span className="text-xs text-gray-400 line-through mb-1">
                              ৳{(product.price * 1.25).toFixed(0)}
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5 mb-4">
                            <div className="flex text-yellow-400 text-xs">
                              ★★★★☆
                            </div>

                            <span className="text-xs text-gray-500">
                              {Number(product.rating || 0).toFixed(1)} (2,847)
                            </span>
                          </div>

                          <div className="text-xs text-gray-600 mb-5 flex items-center gap-1">
                            {product.marketplace_name}

                            {product.is_verified && (
                              <span className="text-green-600 font-semibold">
                                ✓
                              </span>
                            )}
                          </div>

                        <div className="text-xs text-gray-600 mb-5 flex items-center gap-2">
                          <span>{product.marketplace_name}</span>
                             <VerifiedBadge verified={product.is_verified} />
                        </div>


                          {/* SUBTASK 1: PRICE TRACKING */}
                          <TrackProductForm
                            productId={product.id}
                            currentLowestPrice={product.price}
                          />

                          {/* Compare + Save */}
                          <div className="flex gap-3">
                            <button className="flex-1 flex items-center justify-center gap-2 py-2 border border-gray-200 rounded-md text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors">
                              <svg
                                className="w-3.5 h-3.5"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth="2"
                                  d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                                />
                              </svg>
                              Compare
                            </button>

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
