
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

const API_BASE_URL = "http://localhost:8000";

const RentalDetails = () => {
  const { productId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const product = location.state?.product;

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [availability, setAvailability] = useState(null);
  const [checkingAvailability, setCheckingAvailability] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const today = new Date();

  const minDate = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0"),
  ].join("-");

  const rentalDays = useMemo(() => {
    if (!startDate || !endDate || endDate <= startDate) {
      return 0;
    }

    const start = new Date(startDate + "T00:00:00");
    const end = new Date(endDate + "T00:00:00");
    const difference = end.getTime() - start.getTime();

    return Math.round(difference / (1000 * 60 * 60 * 24));
  }, [startDate, endDate]);

  const dailyRate = Number(product?.price || 0);
  const totalCost = rentalDays * dailyRate;

  useEffect(() => {
    if (!productId || !startDate || !endDate || rentalDays <= 0) {
      setAvailability(null);
      setCheckingAvailability(false);
      return;
    }

    const controller = new AbortController();

    const checkAvailability = async () => {
      setCheckingAvailability(true);
      setAvailability(null);
      setError("");

      try {
        const params = new URLSearchParams({
          start_date: startDate,
          end_date: endDate,
        });

        const response = await fetch(
          `${API_BASE_URL}/rentals/${encodeURIComponent(productId)}/availability?${params}`,
          { signal: controller.signal }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || "Could not check rental availability."
          );
        }

        setAvailability(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Availability check failed.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setCheckingAvailability(false);
        }
      }
    };

    checkAvailability();

    return () => controller.abort();
  }, [productId, startDate, endDate, rentalDays]);

  const handleStartDateChange = (event) => {
    const value = event.target.value;

    setStartDate(value);

    if (endDate && endDate <= value) {
      setEndDate("");
    }

    setAvailability(null);
    setError("");
    setMessage("");
  };

  const handleEndDateChange = (event) => {
    setEndDate(event.target.value);
    setAvailability(null);
    setError("");
    setMessage("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setMessage("");

    if (!product || !productId) {
      setError("Product details are missing. Please select the product again.");
      return;
    }

    if (!startDate || !endDate || rentalDays <= 0) {
      setError("Please select a valid start date and end date.");
      return;
    }

    if (availability?.available !== true) {
      setError("The selected dates have not been confirmed as available.");
      return;
    }

    setSubmitting(true);

    try {
      const token = localStorage.getItem("access_token");

      const headers = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE_URL}/rentals/requests`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          product_id: productId,
          start_date: startDate,
          end_date: endDate,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not submit rental request."
        );
      }

      setMessage(
        `Rental request submitted successfully. Status: ${data.status || "pending"}`
      );
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#F8F9FA] p-6 md:p-10">
      <div className="mx-auto max-w-3xl">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-6 text-sm text-gray-600 hover:text-gray-900"
        >
          ← Back
        </button>

        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm md:p-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Rental Details
          </h1>

          <p className="mt-2 text-sm text-gray-500">
            Choose your rental dates and submit a request.
          </p>

          <div className="mt-6 rounded-lg bg-gray-50 p-4">
            <h2 className="font-semibold text-gray-900">
              {product?.name || "Selected product"}
            </h2>

            <p className="mt-1 text-sm text-gray-600">
              Product ID: {productId}
            </p>

            <p className="mt-2 text-lg font-bold text-gray-900">
              ৳{dailyRate.toLocaleString("en-BD")} per day
            </p>

            {!product && (
              <p className="mt-2 text-sm text-amber-700">
                Product details are missing. Go back and select the product
                again.
              </p>
            )}
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="startDate"
                  className="mb-2 block text-sm font-medium text-gray-700"
                >
                  Rental start date
                </label>

                <input
                  id="startDate"
                  type="date"
                  min={minDate}
                  value={startDate}
                  onChange={handleStartDateChange}
                  required
                  className="w-full rounded-md border border-gray-300 p-3 text-sm"
                />
              </div>

              <div>
                <label
                  htmlFor="endDate"
                  className="mb-2 block text-sm font-medium text-gray-700"
                >
                  Rental end date
                </label>

                <input
                  id="endDate"
                  type="date"
                  min={startDate || minDate}
                  value={endDate}
                  onChange={handleEndDateChange}
                  required
                  className="w-full rounded-md border border-gray-300 p-3 text-sm"
                />
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 p-4">
              <div className="flex justify-between gap-4 text-sm text-gray-600">
                <span>Rental duration</span>
                <span>
                  {rentalDays} {rentalDays === 1 ? "day" : "days"}
                </span>
              </div>

              <div className="mt-3 flex justify-between gap-4 text-sm text-gray-600">
                <span>Daily rate</span>
                <span>৳{dailyRate.toLocaleString("en-BD")}</span>
              </div>

              <div className="mt-4 flex justify-between gap-4 border-t border-gray-200 pt-4">
                <span className="font-semibold text-gray-900">
                  Estimated total
                </span>

                <span className="text-xl font-bold text-gray-900">
                  ৳{totalCost.toLocaleString("en-BD")}
                </span>
              </div>

              <p className="mt-2 text-xs text-gray-500">
                The estimated total assumes the product price is a daily
                rental rate.
              </p>
            </div>

            {checkingAvailability && (
              <p className="text-sm text-gray-600">
                Checking availability...
              </p>
            )}

            {availability && (
              <p
                className={`rounded-md p-3 text-sm ${
                  availability.available
                    ? "bg-green-50 text-green-700"
                    : "bg-amber-50 text-amber-700"
                }`}
              >
                {availability.available
                  ? "This product is available for your selected dates."
                  : "This product is not available for your selected dates."}
              </p>
            )}

            {error && (
              <p
                role="alert"
                className="rounded-md bg-red-50 p-3 text-sm text-red-700"
              >
                {error}
              </p>
            )}

            {message && (
              <p
                role="status"
                className="rounded-md bg-green-50 p-3 text-sm text-green-700"
              >
                {message}
              </p>
            )}

            <button
              type="submit"
              disabled={
                submitting ||
                checkingAvailability ||
                !product ||
                rentalDays <= 0 ||
                availability?.available !== true
              }
              className="w-full rounded-md bg-gray-900 px-5 py-3 text-sm font-semibold text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Submitting request..." : "Submit Rental Request"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
};

export default RentalDetails;
