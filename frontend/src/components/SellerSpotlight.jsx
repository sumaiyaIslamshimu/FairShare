import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getSpotlightSellers } from "../api/promotionsApi";

const WINDOW_SIZE = 5;

export default function SellerSpotlight() {
  const [sellers, setSellers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    let isCancelled = false;

    async function load() {
      try {
        const data = await getSpotlightSellers();
        if (!isCancelled) setSellers(data || []);
      } catch (err) {
        if (!isCancelled) setError(err.message);
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      isCancelled = true;
    };
  }, []);

  // Nobody qualifies: hide the section instead of showing an empty box.
  if (!isLoading && !error && sellers.length === 0) return null;

  const total = sellers.length;
  const canRotate = total > WINDOW_SIZE;
  const visibleSellers = canRotate
    ? Array.from({ length: WINDOW_SIZE }, (_, i) => sellers[(offset + i) % total])
    : sellers;

  function rotate(direction) {
    setOffset((current) => (((current + direction * WINDOW_SIZE) % total) + total) % total);
  }

  return (
    <section aria-labelledby="seller-spotlight-heading" className="mb-8">
      <div className="flex items-center justify-between gap-3 mb-4">
        <h2 id="seller-spotlight-heading" className="text-xl font-semibold text-gray-900">
          Seller Spotlight
        </h2>

        {canRotate && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => rotate(-1)}
              aria-label="Show previous sellers"
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              type="button"
              onClick={() => rotate(1)}
              aria-label="Show next sellers"
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading featured sellers...</p>}

      {!isLoading && error && (
        <p className="text-sm text-red-600">Could not load featured sellers. {error}</p>
      )}

      {!isLoading && !error && (
        <ul
          aria-live="polite"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4"
        >
          {visibleSellers.map((seller) => (
            <li
              key={seller.seller_id}
              className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 flex flex-col"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-semibold text-gray-900">{seller.business_name}</h3>
                {seller.is_verified === true && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full whitespace-nowrap">
                    ✓ Verified
                  </span>
                )}
              </div>

              {seller.rating !== null && seller.rating !== undefined && (
                <p className="text-sm text-gray-700 mb-2">
                  <span className="text-yellow-500">★</span> {seller.rating}
                </p>
              )}

              {seller.description && (
                <p className="text-sm text-gray-500 mb-3">{seller.description}</p>
              )}

              {seller.listing_count !== undefined && (
                <p className="text-xs text-gray-400 mt-auto mb-3">
                  {seller.listing_count} {seller.listing_count === 1 ? "listing" : "listings"}
                </p>
              )}

              <Link
                to={`/?seller_id=${encodeURIComponent(seller.seller_id)}`}
                className="text-center px-3 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800"
              >
                View listings
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}