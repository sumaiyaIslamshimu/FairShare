import "./PriceInsights.css";
import { useState, useEffect } from "react";

const API_BASE = "http://127.0.0.1:8000";
const CURRENCY = "৳";

function comparisonLine(own, average) {
  if (own < average * 0.98) {
    return { text: "Your price is below average", tone: "good" };
  }
  if (own > average * 1.02) {
    return { text: "Your price is above average", tone: "warn" };
  }
  return { text: "Your price is close to the average", tone: "neutral" };
}

export function PriceInsightsView({ data }) {
  if (!data.has_competitors) {
    return (
      <p className="insights-empty">
        No other sellers list this product.
      </p>
    );
  }

  const line = comparisonLine(data.own_price, data.average);

  return (
    <>
      <div className="insights-row">
        <div className="insight-box">
          <div className="insight-number">{CURRENCY}{data.lowest}</div>
          <div className="insight-label">Lowest</div>
        </div>

        <div className="insight-box">
          <div className="insight-number">{CURRENCY}{data.average}</div>
          <div className="insight-label">Average</div>
        </div>

        <div className="insight-box">
          <div className="insight-number">{CURRENCY}{data.highest}</div>
          <div className="insight-label">Highest</div>
        </div>
      </div>

      <p className={`insight-comparison ${line.tone}`}>
        {line.text} (yours: {CURRENCY}{data.own_price})
      </p>
    </>
  );
}

function PriceInsights({ listingId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError("");
    setData(null);

    const token = localStorage.getItem("fairshare_token");

    fetch(`${API_BASE}/seller/listings/${listingId}/price-insights`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Could not load price insights.");
        }
        return res.json();
      })
      .then((json) => {
        if (!cancelled) setData(json);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [listingId]);

  return (
    <div className="insights-card">
      <h2>Price insights</h2>
      {loading && <p className="insights-empty">Loading...</p>}
      {error && <p className="field-error">{error}</p>}
      {data && <PriceInsightsView data={data} />}
    </div>
  );
}

export default PriceInsights;