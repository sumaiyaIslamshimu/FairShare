import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ListingForm from "../components/ListingForm";
import DiscountSection from "../components/DiscountSection";
import {
  getSellerListings,
  createSellerListing,
  updateSellerListing,
} from "../api/sellerListingsApi";

// Handles both /seller/listings/new and /seller/listings/:id/edit
export default function SellerListingFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [initialValues, setInitialValues] = useState(null);
  const [isLoading, setIsLoading] = useState(isEdit);
  const [loadError, setLoadError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState("");

  useEffect(() => {
    if (!isEdit) return;
    let isCancelled = false;

    async function load() {
      try {
        // Only the logged-in seller's own listings are ever fetched, so a
        // listing that isn't theirs simply won't be found here.
        const all = await getSellerListings();
        if (isCancelled) return;
        const found = all.find((l) => String(l.id) === String(id));
        if (!found) {
          setLoadError("Listing not found");
        } else {
          setInitialValues(found);
        }
      } catch (err) {
        if (!isCancelled) setLoadError(err.message);
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      isCancelled = true;
    };
  }, [id, isEdit]);

  async function handleSubmit(payload) {
    setIsSubmitting(true);
    setServerError("");
    try {
      if (isEdit) {
        await updateSellerListing(id, payload);
      } else {
        await createSellerListing(payload);
      }
      navigate("/seller/dashboard");
    } catch (err) {
      setServerError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

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

      <main className="max-w-2xl mx-auto px-6 py-8">
        <Link
          to="/seller/dashboard"
          className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 mb-6"
        >
          ← Back to my listings
        </Link>

        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          {isEdit ? "Edit Listing" : "Add Listing"}
        </h1>

        {isLoading && <div className="text-center py-10 text-gray-500">Loading listing...</div>}

        {!isLoading && loadError && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
            {loadError}
          </div>
        )}

        {!isLoading && !loadError && (
          <>
            <ListingForm
              initialValues={initialValues}
              onSubmit={handleSubmit}
              onCancel={() => navigate("/seller/dashboard")}
              isSubmitting={isSubmitting}
              serverError={serverError}
            />

            {isEdit ? (
              <DiscountSection
                listingId={id}
                originalPrice={initialValues ? initialValues.price : 0}
              />
            ) : (
              <p className="text-sm text-gray-500 mt-4">
                Save this listing first, then edit it to run a discount.
              </p>
            )}
          </>
        )}
      </main>
    </div>
  );
}