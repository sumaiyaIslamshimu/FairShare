import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getProductRanking } from "../api/productsApi";
import RecommendationsSection from "../components/RecommendationsSection";

export default function ProductDetailsPage() {
  const { productId } = useParams();

  const [product, setProduct] = useState(null);
  const [listings, setListings] = useState([]); // backend best-value order
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);

  const [sortMode, setSortMode] = useState("best_value"); // "best_value" | "lowest_price"
  const [expandedListingId, setExpandedListingId] = useState(null);
  const storedBudget = sessionStorage.getItem("fairshare_budget");
  const budget = storedBudget ? Number(storedBudget) : null;

  useEffect(() => {
    let isCancelled = false;

    async function loadRanking() {
      setIsLoading(true);
      setError("");
      setNotFound(false);

      try {
        const data = await getProductRanking(productId);
        if (isCancelled) return;
        setProduct(data.product);
        setListings(data.listings || []);
      } catch (err) {
        if (isCancelled) return;
        if (err.message === "Product not found") {
          setNotFound(true);
        } else {
          setError(err.message || "Failed to load best-value ranking. Please try again.");
        }
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    }

    loadRanking();

    return () => {
      isCancelled = true;
    };
  }, [productId]);

  // Backend returns listings sorted by score descending, so the
  // highest-scoring listing is always listings[0] — captured once,
  // before any local toggle-sort, so the badge stays attached to it.
  const bestValueListingId = listings.length > 0 ? listings[0].id : null;
  const currentPrice =
  listings.length > 0
    ? Math.min(...listings.map((listing) => listing.price))
    : null;
  const displayedListings =
    sortMode === "lowest_price"
      ? [...listings].sort((a, b) => a.price - b.price)
      : listings;

  function toggleBreakdown(listingId) {
    setExpandedListingId((current) => (current === listingId ? null : listingId));
  }

  return (
    <div className="min-h-screen bg-white">
      {/* FairShare Navbar */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-gray-200 bg-white">
        <Link to="/" className="flex items-center gap-2 no-underline">
          <span className="w-7 h-7 rounded-lg bg-slate-900 flex items-center justify-center text-sm">
            🛍️
          </span>

          <span className="text-lg font-bold text-slate-900">
            FairShare
          </span>
        </Link>
      </nav>

      <div className="p-6 max-w-5xl mx-auto">
        {/* Back to Results */}
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 mb-6"
        >
          ← Back to results
        </Link>

        {isLoading && (
          <div className="text-center text-gray-500 mt-20">
            Loading best-value ranking...
          </div>
        )}

        {!isLoading && notFound && (
          <div className="text-center text-gray-700 mt-20">
            <p className="text-xl font-semibold mb-2">Product not found</p>
            <p className="text-sm text-gray-500">
              This product may have been removed or the link is incorrect.
            </p>
          </div>
        )}

        {!isLoading && !notFound && error && (
          <div className="text-center text-red-500 mt-20">
            <p className="font-semibold mb-1">Failed to load best-value ranking. Please try again.</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {!isLoading && !notFound && !error && product && (
          <>
            {/* Product Header */}
            <div className="flex flex-col md:flex-row gap-6 bg-white border border-gray-200 rounded-lg shadow-sm p-6 mb-8">
              <div className="w-full md:w-64 h-64 flex-shrink-0 bg-gray-100 rounded-lg overflow-hidden">
                <img
                  src={
                    product.image_url ||
                    `https://placehold.co/600x450/f3f4f6/a1a1aa?text=${encodeURIComponent(product.category || "Product")}`
                  }
                  alt={product.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src = `https://placehold.co/600x450/f3f4f6/a1a1aa?text=${encodeURIComponent(product.category || "Product")}`;
                  }}
                />
              </div>

              <div className="flex flex-col justify-center">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">
                  {product.name}
                </h1>

                <p className="text-sm text-gray-500 mb-1">
                  Brand:{" "}
                  <span className="text-gray-900 font-medium">
                    {product.brand}
                  </span>
                </p>

                <p className="text-sm text-gray-500">
                  Category:{" "}
                  <span className="text-gray-900 font-medium">
                    {product.category}
                  </span>
                </p>
              </div>
            </div>

            {/* Seller Comparison Section */}
            <div>
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  Compare Sellers
                </h2>

                {/* Order toggle */}
                <div className="inline-flex border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setSortMode("best_value")}
                    className={`px-4 py-2 text-sm font-medium ${
                      sortMode === "best_value"
                        ? "bg-gray-900 text-white"
                        : "bg-white text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    Best value
                  </button>
                  <button
                    type="button"
                    onClick={() => setSortMode("lowest_price")}
                    className={`px-4 py-2 text-sm font-medium border-l border-gray-200 ${
                      sortMode === "lowest_price"
                        ? "bg-gray-900 text-white"
                        : "bg-white text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    Lowest price
                  </button>
                </div>
              </div>

              {listings.length === 1 && (
                <p className="text-sm text-gray-500 mb-4">
                  No other marketplace lists this product.
                </p>
              )}

              {/* Desktop Seller Table */}
              <div className="hidden md:block border border-gray-200 rounded-lg overflow-hidden">
                <div className="grid grid-cols-6 bg-gray-50 text-xs font-semibold text-gray-500 uppercase px-4 py-3">
                  <span className="col-span-2">Seller</span>
                  <span>Price</span>
                  <span>Rating</span>
                  <span>Best Value Score</span>
                  <span className="text-right">Action</span>
                </div>

                {displayedListings.map((listing) => {
                  const isBestValue = listing.id === bestValueListingId;
                  const isExpanded = expandedListingId === listing.id;

                  return (
                    <div key={listing.id} className="border-t border-gray-100">
                      <div className="grid grid-cols-6 items-center px-4 py-4">
                        <div className="col-span-2 flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {listing.marketplace}
                          </span>

                          {isBestValue && (
                            <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full whitespace-nowrap">
                              Best value
                            </span>
                          )}
                        </div>

                        <span className="font-bold text-gray-900">
                          ৳{listing.price.toLocaleString()}
                        </span>

                        <span className="text-sm text-gray-600">
                          ★ {listing.rating}
                        </span>

                        <div>
                          <button
                            type="button"
                            onClick={() => toggleBreakdown(listing.id)}
                            className="font-bold text-gray-900 underline decoration-dotted text-left"
                          >
                            {listing.score}
                          </button>
                        </div>

                        <div className="text-right">
                          {listing.product_url ? (
                            <a
                              href={listing.product_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-4 py-2 rounded font-medium text-sm bg-gray-900 text-white hover:bg-gray-800 inline-block"
                            >
                              View
                            </a>
                          ) : (
                            <span className="px-4 py-2 rounded font-medium text-sm bg-gray-200 text-gray-500 inline-block">
                              Link unavailable
                            </span>
                          )}
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="px-4 py-4 bg-gray-50 border-t border-gray-100">
                          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
                            Score breakdown
                          </p>
                          <div className="grid grid-cols-4 gap-4 text-sm text-gray-700">
                            <span>Price: {listing.score_breakdown.price_points} / 40</span>
                            <span>Rating: {listing.score_breakdown.rating_points} / 25</span>
                            <span>Delivery: {listing.score_breakdown.delivery_points} / 15</span>
                            <span>Discount: {listing.score_breakdown.discount_points} / 20</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Mobile Seller Cards */}
              <div className="md:hidden space-y-4">
                {displayedListings.map((listing) => {
                  const isBestValue = listing.id === bestValueListingId;
                  const isExpanded = expandedListingId === listing.id;

                  return (
                    <div
                      key={listing.id}
                      className="border border-gray-200 rounded-lg shadow-sm bg-white p-4"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <span className="font-medium text-gray-900">
                          {listing.marketplace}
                        </span>

                        {isBestValue && (
                          <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full whitespace-nowrap">
                            Best value
                          </span>
                        )}
                      </div>

                      <div className="flex justify-between items-end mb-3">
                        <div>
                          <p className="text-xs text-gray-500 mb-1">
                            Price
                          </p>

                          <p className="font-bold text-lg text-gray-900">
                            ৳{listing.price.toLocaleString()}
                          </p>

                          <p className="text-xs text-gray-500 mt-1">
                            ★ {listing.rating}
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={() => toggleBreakdown(listing.id)}
                          className="text-right"
                        >
                          <p className="text-xs text-gray-500 mb-1">Best Value Score</p>
                          <p className="font-bold text-lg text-gray-900 underline decoration-dotted">
                            {listing.score}
                          </p>
                        </button>
                      </div>

                      {isExpanded && (
                        <div className="mb-3 bg-gray-50 border border-gray-100 rounded-lg p-3 text-sm text-gray-700 space-y-1">
                          <p className="text-xs font-semibold text-gray-500 uppercase mb-1">
                            Score breakdown
                          </p>
                          <p>Price: {listing.score_breakdown.price_points} / 40</p>
                          <p>Rating: {listing.score_breakdown.rating_points} / 25</p>
                          <p>Delivery: {listing.score_breakdown.delivery_points} / 15</p>
                          <p>Discount: {listing.score_breakdown.discount_points} / 20</p>
                        </div>
                      )}

                      {listing.product_url ? (
                        <a
                          href={listing.product_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-center px-4 py-2 rounded font-medium text-sm bg-gray-900 text-white hover:bg-gray-800"
                        >
                          View
                        </a>
                      ) : (
                        <span className="block text-center px-4 py-2 rounded font-medium text-sm bg-gray-200 text-gray-500">
                          Link unavailable
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
             </div>

            <RecommendationsSection
              productId={product._id || product.id}
              budget={budget}
              currentPrice={currentPrice}
            />
          </>
          </>
        )}
      </div>
    </div>
  );
}