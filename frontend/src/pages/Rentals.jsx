import { useState, useEffect } from "react";
import ShopperLayout from "../components/ShopperLayout";
import RentalFilterBar from "../components/RentalFilterBar";
import RentalCard from "../components/RentalCard";
import "./Rentals.css";

const API_BASE = "http://127.0.0.1:8000";

function Rentals() {
  const [filters, setFilters] = useState({
    q: "",
    category: "",
    maxPrice: "",
  });

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const timer = setTimeout(() => {
      const params = new URLSearchParams();

      if (filters.q.trim()) {
        params.set("q", filters.q.trim());
      }

      if (filters.category) {
        params.set("category", filters.category);
      }

      if (Number(filters.maxPrice) > 0) {
        params.set("maxPricePerDay", filters.maxPrice);
      }

      setLoading(true);
      setError("");

      fetch(`${API_BASE}/rentals/search?${params.toString()}`)
        .then((res) => {
          if (!res.ok) {
            throw new Error("Could not load rental items.");
          }

          return res.json();
        })
        .then((data) => {
          if (!cancelled) {
            setItems(data);
          }
        })
        .catch((err) => {
          if (!cancelled) {
            setError(err.message);
          }
        })
        .finally(() => {
          if (!cancelled) {
            setLoading(false);
          }
        });
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [filters]);

  return (
    <ShopperLayout
      activePage="rentals"
      pageTitle="Rental Marketplace"
    >
      <p className="rentals-subtitle">
        Browse rentals or list your own unused items
      </p>

      <RentalFilterBar
        filters={filters}
        onChange={setFilters}
      />

      {loading && (
        <p className="status-text">
          Loading rental items...
        </p>
      )}

      {error && (
        <p className="status-text error">
          {error}
        </p>
      )}

      {!loading && !error && items.length === 0 && (
        <p className="status-text">
          No rental items found
        </p>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="rentals-grid">
          {items.map((item) => (
            <RentalCard
              key={item.id}
              item={item}
            />
          ))}
        </div>
      )}
    </ShopperLayout>
  );
}

export default Rentals;