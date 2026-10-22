import { useEffect, useState } from "react";
import { getSellerInsights } from "../../api/seller.js";
import { formatPrice } from "../../utils/format.js";

export default function Insights() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getSellerInsights()
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <div style={{ color: "red" }}>{error}</div>;
  if (!data) return <div>Loading analytics...</div>;

  return (
    <div>
      <h2>Seller Insights</h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ padding: "1rem", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "8px" }}>
          <h3>Total Revenue</h3>
          <p style={{ fontSize: "1.5rem", fontWeight: "bold" }}>{formatPrice(data.total_revenue_paisa, "BDT")}</p>
        </div>
        <div style={{ padding: "1rem", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "8px" }}>
          <h3>Units Sold</h3>
          <p style={{ fontSize: "1.5rem", fontWeight: "bold" }}>{data.total_units_sold}</p>
        </div>
        <div style={{ padding: "1rem", background: "#fef3c7", border: "1px solid #fde68a", borderRadius: "8px" }}>
          <h3>Products</h3>
          <p>Total: {data.total_products} | Active: {data.active_products}</p>
          <p>Out of Stock: {data.out_of_stock_products}</p>
        </div>
        <div style={{ padding: "1rem", background: "#f3e8ff", border: "1px solid #e9d5ff", borderRadius: "8px" }}>
          <h3>Order Status Summary</h3>
          <ul>
            {Object.entries(data.orders_by_status).map(([status, count]) => (
              <li key={status} style={{ textTransform: "capitalize" }}>{status}: {count}</li>
            ))}
          </ul>
        </div>
      </div>

      <h3>Low Stock Alerts (≤ 5 units left)</h3>
      {data.low_stock_items.length === 0 ? (
        <p>Inventory looks good!</p>
      ) : (
        <ul>
          {data.low_stock_items.map(item => (
            <li key={item.id} style={{ color: "red", fontWeight: "bold" }}>
              {item.title} - Only {item.stock_qty} left in stock!
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}