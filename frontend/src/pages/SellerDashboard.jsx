import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getSellerListings, deleteSellerListing } from "../../api/sellerListingsApi";
import { getStockStatus } from "../../utils/listingValidation";

function placeholderImage(category) {
  return `https://placehold.co/80x80/f3f4f6/a1a1aa?text=${encodeURIComponent(category || "Item")}`;
}

function Thumbnail({ listing }) {
  return (
    <img
      src={listing.image_link || placeholderImage(listing.category)}
      alt={listing.name}
      className="w-14 h-14 rounded-lg object-cover bg-gray-100"
      onError={(e) => {
        e.currentTarget.onerror = null;
        e.currentTarget.src = placeholderImage(listing.category);
      }}
    />
  );
}

export default function SellerDashboard() {
  const navigate = useNavigate();

  const [listings, setListings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const [pendingDelete, setPendingDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  useEffect(() => {
    let isCancelled = false;

    async function load() {
      setIsLoading(true);
      setError("");
      try {
        const data = await getSellerListings();
        if (!isCancelled) setListings(data);
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

  async function confirmDelete() {
    setIsDeleting(true);
    setDeleteError("");
    try {
      await deleteSellerListing(pendingDelete.id);
      setListings((prev) => prev.filter((l) => l.id !== pendingDelete.id));
      setPendingDelete(null);
    } catch (err) {
      setDeleteError(err.message);
    } finally {
      setIsDeleting(false);
    }
  }

  const goToAdd = () => navigate("/seller/listings/new");
  const goToEdit = (id) => navigate(`/seller/listings/${id}/edit`);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="flex items-center justify-between px-8 py-4 border-b border-gray-200 bg-white">
        <Link to="/" className="flex items-center gap-2 no-underline">
          <span className="w-7 h-7 rounded-lg bg-slate-900 flex items-center justify-center text-sm">
            🛍️
          </span>
          <span className="text-lg font-bold text-slate-900">FairShare</span>
        </Link>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <h1 className="text-3xl font-bold text-gray-900">My Listings</h1>
          <button
            onClick={goToAdd}
            className="px-5 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
          >
            Add Listing
          </button>
        </div>

        {isLoading && <div className="text-center py-10 text-gray-500">Loading listings...</div>}

        {!isLoading && error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">{error}</div>
        )}

        {!isLoading && !error && listings.length === 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-10 text-center">
            <p className="text-gray-600 mb-4">You don't have any listings yet.</p>
            <button
              onClick={goToAdd}
              className="px-5 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
            >
              Add your first listing
            </button>
          </div>
        )}

        {!isLoading && !error && listings.length > 0 && (
          <>
            {/* Desktop table */}
            <div className="hidden md:block bg-white border border-gray-200 rounded-lg overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                  <tr>
                    <th className="text-left px-4 py-3">Image</th>
                    <th className="text-left px-4 py-3">Product name</th>
                    <th className="text-left px-4 py-3">Category</th>
                    <th className="text-left px-4 py-3">Price</th>
                    <th className="text-left px-4 py-3">Stock</th>
                    <th className="text-left px-4 py-3">Status</th>
                    <th className="text-right px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {listings.map((listing) => {
                    const status = getStockStatus(listing.stock);
                    return (
                      <tr key={listing.id} className="border-t border-gray-100">
                        <td className="px-4 py-3">
                          <Thumbnail listing={listing} />
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900">{listing.name}</td>
                        <td className="px-4 py-3 text-gray-600">{listing.category}</td>
                        <td className="px-4 py-3 font-bold text-gray-900">
                          ৳{Number(listing.price).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-gray-700">{listing.stock}</td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-1 rounded-full whitespace-nowrap ${status.className}`}>
                            {status.label}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                          <button
                            onClick={() => goToEdit(listing.id)}
                            className="px-3 py-2 border border-gray-300 rounded-lg text-sm mr-2 hover:bg-gray-50"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => {
                              setDeleteError("");
                              setPendingDelete(listing);
                            }}
                            className="px-3 py-2 border border-red-300 text-red-600 rounded-lg text-sm hover:bg-red-50"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="md:hidden space-y-4">
              {listings.map((listing) => {
                const status = getStockStatus(listing.stock);
                return (
                  <div
                    key={listing.id}
                    className="bg-white border border-gray-200 rounded-lg shadow-sm p-4"
                  >
                    <div className="flex gap-3 mb-3">
                      <Thumbnail listing={listing} />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{listing.name}</p>
                        <p className="text-sm text-gray-500">{listing.category}</p>
                      </div>
                      <span
                        className={`self-start text-xs px-2 py-1 rounded-full whitespace-nowrap ${status.className}`}
                      >
                        {status.label}
                      </span>
                    </div>

                    <div className="flex justify-between text-sm mb-3">
                      <span className="font-bold text-gray-900">
                        ৳{Number(listing.price).toLocaleString()}
                      </span>
                      <span className="text-gray-600">Stock: {listing.stock}</span>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => goToEdit(listing.id)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => {
                          setDeleteError("");
                          setPendingDelete(listing);
                        }}
                        className="flex-1 px-3 py-2 border border-red-300 text-red-600 rounded-lg text-sm hover:bg-red-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </main>

      {/* Delete confirmation */}
      {pendingDelete && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-sm">
            <p className="text-gray-900 font-medium mb-1">
              Delete this listing? This cannot be undone.
            </p>
            <p className="text-sm text-gray-500 mb-4">{pendingDelete.name}</p>

            {deleteError && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm mb-4">
                {deleteError}
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setPendingDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 disabled:opacity-60"
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}