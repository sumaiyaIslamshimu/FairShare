import TrackProductForm from "../components/TrackProductForm";
import { useState, useEffect } from "react";
import SuggestedForYou from "../components/SuggestedForYou";
import VerifiedBadge from "../components/VerifiedBadge";

const ProductSearchPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [sort, setSort] = useState("Most Relevant");

  const [selectedBrands, setSelectedBrands] = useState({
    Apple: false,
    Samsung: false,
    Sony: false,
    Logitech: false,
    Dell: false,
    Bose: false,
    Lotto: false,
  });

  // Fetch products whenever a filter changes
  useEffect(() => {
    const fetchFilteredProducts = async () => {
      setLoading(true);
      setError(null);

      try {
        const activeBrands = Object.keys(selectedBrands)
          .filter((brand) => selectedBrands[brand])
          .join(",");

        const params = new URLSearchParams();

        if (searchQuery) {
          params.append("q", searchQuery);
        }

        if (minPrice) {
          params.append("min_price", minPrice);
        }

        if (maxPrice) {
          params.append("max_price", maxPrice);
        }

        if (activeBrands) {
          params.append("brand", activeBrands);
        }

        if (sort !== "Most Relevant") {
          params.append("sort", sort);
        }

        const response = await fetch(
          `http://localhost:8000/products/search?${params.toString()}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch products.");
        }

        const data = await response.json();
        setProducts(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Debounce API requests while typing/filtering
    const delayDebounceFn = setTimeout(() => {
      fetchFilteredProducts();
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, minPrice, maxPrice, sort, selectedBrands]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
  };

  const handleBrandChange = (brand) => {
    setSelectedBrands((prev) => ({
      ...prev,
      [brand]: !prev[brand],
    }));
  };

  const getCardColor = (index) => {
    const colors = [
      "bg-[#FFC107]",
      "bg-[#1F1F1F]",
      "bg-[#1E293B]",
      "bg-[#9CA3AF]",
    ];

    return colors[index % colors.length];
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col font-sans">
      {/* TOP NAVIGATION BAR */}
      <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0 z-10">
        <div className="flex items-center gap-3 w-64">
          <div className="w-8 h-8 bg-gray-900 rounded flex items-center justify-center">
            <div className="w-3 h-3 bg-white rounded-full"></div>
          </div>

          <div>
            <h1 className="font-bold text-gray-900 leading-tight">
              FairShare
            </h1>
            <p className="text-[10px] text-gray-500 leading-none">
              Shopper
            </p>
          </div>
        </div>

        <div className="flex-1 max-w-2xl px-4">
          <div className="relative">
            <svg
              className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>

            <input
              type="text"
              placeholder="Search products, brands..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-md text-sm outline-none focus:bg-white focus:border-gray-300 transition-colors"
            />
          </div>
        </div>

        <div className="flex items-center gap-4 w-64 justify-end">
          <button className="text-gray-400 hover:text-gray-600 relative">
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
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>

            <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
          </button>

          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-bold text-gray-600">
              AJ
            </div>

            <div className="hidden md:block">
              <p className="text-sm font-semibold text-gray-900 leading-tight">
                Alex Johnson
              </p>
              <p className="text-[10px] text-gray-500 leading-none">
                Shopper
              </p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT DASHBOARD SIDEBAR */}
        <aside className="w-64 bg-white border-r border-gray-200 py-6 flex flex-col overflow-y-auto hidden md:flex shrink-0">
          <nav className="flex flex-col gap-1 px-4">
            <a
              href="/shopper/home"
              className="flex items-center gap-3 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md"
            >
              <span>🏠</span>
              Home
            </a>

            <a
              href="/shopper/search"
              className="flex items-center gap-3 px-3 py-2 text-sm font-semibold text-gray-900 bg-gray-50 rounded-md"
            >
              <span>🔍</span>
              Search & Browse
            </a>

            {[
              ["⇄", "Compare", "/shopper/compare"],
              ["✨", "Recommendations", "/shopper/recommendations"],
              ["📈", "Price Tracking", "/shopper/price-tracking"],
              ["🏠", "Rentals", "/shopper/rentals"],
              ["💬", "Messages", "/shopper/messages"],
              ["🔔", "Notifications", "/shopper/notifications"],
              ["👤", "Profile", "/shopper/profile"],
            ].map(([icon, label, href]) => (
              <a
                key={label}
                href={href}
                className="flex items-center gap-3 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md"
              >
                <span>{icon}</span>
                {label}
              </a>
            ))}
          </nav>
        </aside>

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-6xl mx-auto">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Search & Browse
              </h2>

              <p className="text-sm text-gray-500 mt-1">
                Discover the best deals across all sellers
              </p>
            </div>
            <SuggestedForYou />
            {/* SEARCH BAR */}
            <form onSubmit={handleSearchSubmit} className="mb-8">
              <div className="flex items-center bg-white border border-gray-300 rounded-lg p-1.5 shadow-sm">
                <div className="px-3 text-gray-400">
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
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>

                <input
                  type="text"
                  placeholder="Search product name, brand or category..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 py-2 outline-none text-sm text-gray-800"
                />

                <button
                  type="submit"
                  className="bg-[#111827] text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-gray-800 transition-colors"
                >
                  Search
                </button>
              </div>
            </form>

            <div className="flex flex-col lg:flex-row gap-8">
              {/* FILTER SIDEBAR */}
              <div className="w-full lg:w-64 shrink-0 bg-white p-5 rounded-xl border border-gray-200 shadow-sm h-fit">
                {/* Price */}
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3 text-sm">
                    Price Range
                  </h3>

                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={minPrice}
                      onChange={(e) => setMinPrice(e.target.value)}
                      className="w-full p-2 border border-gray-200 rounded text-sm outline-none focus:border-gray-400"
                    />

                    <span className="text-gray-400">-</span>

                    <input
                      type="number"
                      placeholder="Max"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      className="w-full p-2 border border-gray-200 rounded text-sm outline-none focus:border-gray-400"
                    />
                  </div>
                </div>

                {/* Brand */}
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3 text-sm">
                    Brand
                  </h3>

                  <div className="space-y-2.5">
                    {Object.keys(selectedBrands).map((brand) => (
                      <label
                        key={brand}
                        className="flex items-center gap-3 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedBrands[brand]}
                          onChange={() => handleBrandChange(brand)}
                          className="w-4 h-4 rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                        />

                        <span className="text-gray-700 text-sm">
                          {brand}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Rating */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3 text-sm">
                    Rating
                  </h3>

                  <div className="space-y-2.5">
                    {[4, 3, 2].map((stars) => (
                      <label
                        key={stars}
                        className="flex items-center gap-3 cursor-pointer"
                      >
                        <input
                          type="radio"
                          name="rating"
                          className="w-4 h-4 text-gray-900 focus:ring-gray-900 border-gray-300"
                        />

                        <div className="flex items-center gap-1 text-yellow-400 text-sm">
                          {"★".repeat(stars)}
                          {"☆".repeat(5 - stars)}

                          <span className="text-gray-600 text-xs ml-1">
                            & up
                          </span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* PRODUCTS */}
              <div className="flex-1">
                <div className="flex justify-between items-center mb-4 border-b border-gray-200 pb-4">
                  <span className="text-sm text-gray-500">
                    {products.length} products found
                  </span>

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
                                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                                />
                              </svg>
                              Save
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ProductSearchPage;