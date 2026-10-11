import { useEffect, useState } from "react";
import {
  getListingDiscount,
  removeListingDiscount,
  saveListingDiscount,
} from "../api/promotionsApi";
import {
  previewDiscountedPrice,
  toLocalInputValue,
  validateDiscountForm,
} from "../utils/discountUtils";

const EMPTY_FORM = { percentage: "", startsAt: "", endsAt: "" };

const STATUS_BADGES = {
  active: { text: "Active now", className: "bg-green-100 text-green-800" },
  upcoming: { text: "Scheduled", className: "bg-yellow-100 text-yellow-800" },
  expired: { text: "Expired", className: "bg-gray-200 text-gray-600" },
};

function money(amount) {
  return `৳${Number(amount).toLocaleString()}`;
}

// Works on a listing that already exists, so it is shown on the edit page.
export default function DiscountSection({ listingId, originalPrice }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [current, setCurrent] = useState(null); // last discount returned by the server
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const [serverError, setServerError] = useState("");
  const [message, setMessage] = useState("");

  function applyServerView(view) {
    setCurrent(view);
    if (view.has_discount) {
      setForm({
        percentage: String(view.percentage),
        startsAt: toLocalInputValue(view.starts_at),
        endsAt: toLocalInputValue(view.ends_at),
      });
    } else {
      setForm(EMPTY_FORM);
    }
    setErrors({});
  }

  useEffect(() => {
    let isCancelled = false;

    async function load() {
      setIsLoading(true);
      setServerError("");
      try {
        const view = await getListingDiscount(listingId);
        if (!isCancelled) applyServerView(view);
      } catch (err) {
        if (!isCancelled) setServerError(err.message);
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      isCancelled = true;
    };
  }, [listingId]);

  function handleChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setMessage("");
  }

  async function handleSave() {
    setServerError("");
    setMessage("");

    const validationErrors = validateDiscountForm(form);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return; // nothing is sent

    setIsBusy(true);
    try {
      const view = await saveListingDiscount(listingId, {
        percentage: Number(form.percentage),
        starts_at: new Date(form.startsAt).toISOString(),
        ends_at: new Date(form.endsAt).toISOString(),
      });
      applyServerView(view);
      setMessage("Discount saved.");
    } catch (err) {
      setServerError(err.message);
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRemove() {
    setServerError("");
    setMessage("");
    setIsBusy(true);
    try {
      const view = await removeListingDiscount(listingId);
      applyServerView(view);
      setMessage("Discount removed.");
    } catch (err) {
      setServerError(err.message);
    } finally {
      setIsBusy(false);
    }
  }

  const preview = previewDiscountedPrice(originalPrice, form.percentage);
  const badge = current && current.has_discount ? STATUS_BADGES[current.status] : null;

  const inputClass = (field) =>
    `w-full border rounded-lg px-4 py-2 text-sm ${
      errors[field] ? "border-red-500" : "border-gray-300"
    }`;

  return (
    <section
      aria-labelledby="run-discount-heading"
      className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 mt-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
        <h2 id="run-discount-heading" className="text-lg font-semibold text-gray-900">
          Run a discount
        </h2>
        {badge && (
          <span className={`text-xs px-2 py-1 rounded-full ${badge.className}`}>
            {badge.text}
          </span>
        )}
      </div>
      <p className="text-sm text-gray-500 mb-5">
        Set a time-limited discount. Your listing's price stays the same, and
        the discount stops on its own at the end time.
      </p>

      {isLoading && <p className="text-sm text-gray-500">Loading discount...</p>}

      {!isLoading && (
        <div className="space-y-5">
          {serverError && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm">
              {serverError}
            </div>
          )}
          {message && (
            <div className="bg-green-50 border border-green-200 text-green-800 p-3 rounded-lg text-sm">
              {message}
            </div>
          )}

          <div>
            <label htmlFor="discount-percentage" className="block text-sm font-semibold text-gray-900 mb-1">
              Discount percentage (1–90)
            </label>
            <input
              id="discount-percentage"
              type="number"
              step="any"
              value={form.percentage}
              onChange={(e) => handleChange("percentage", e.target.value)}
              className={inputClass("percentage")}
            />
            {errors.percentage && (
              <p className="text-red-500 text-xs mt-1">{errors.percentage}</p>
            )}
            {preview !== null && (
              <p className="text-sm text-gray-700 mt-2">
                Price preview:{" "}
                <span className="line-through text-gray-400">{money(originalPrice)}</span>{" "}
                <span className="font-semibold text-gray-900">{money(preview)}</span>
                <span className="text-gray-400"> (based on the saved price)</span>
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label htmlFor="discount-start" className="block text-sm font-semibold text-gray-900 mb-1">
                Starts
              </label>
              <input
                id="discount-start"
                type="datetime-local"
                value={form.startsAt}
                onChange={(e) => handleChange("startsAt", e.target.value)}
                className={inputClass("startsAt")}
              />
              {errors.startsAt && (
                <p className="text-red-500 text-xs mt-1">{errors.startsAt}</p>
              )}
            </div>

            <div>
              <label htmlFor="discount-end" className="block text-sm font-semibold text-gray-900 mb-1">
                Ends
              </label>
              <input
                id="discount-end"
                type="datetime-local"
                value={form.endsAt}
                onChange={(e) => handleChange("endsAt", e.target.value)}
                className={inputClass("endsAt")}
              />
              {errors.endsAt && (
                <p className="text-red-500 text-xs mt-1">{errors.endsAt}</p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleSave}
              disabled={isBusy}
              className="px-5 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-60"
            >
              {isBusy ? "Saving..." : "Save discount"}
            </button>

            {current && current.has_discount && (
              <button
                type="button"
                onClick={handleRemove}
                disabled={isBusy}
                className="px-5 py-2 border border-red-300 text-red-600 rounded-lg text-sm font-medium hover:bg-red-50 disabled:opacity-60"
              >
                Remove discount
              </button>
            )}
          </div>
        </div>
      )}
    </section>
  );
}