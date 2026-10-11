import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import "./PriceHistoryChart.css";

const API_BASE = "http://127.0.0.1:8000";

const PriceHistoryChart = ({ productId }) => {
  const [priceHistory, setPriceHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPriceHistory = async () => {
      try {
        setLoading(true);

        const response = await fetch(
          `${API_BASE}/products/${productId}/price-history`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch price history");
        }

        const data = await response.json();

        setPriceHistory(data);
      } catch (error) {
        console.log("Price history unavailable:", error);

        // Temporary sample data
        // This will be replaced by real backend data.
        setPriceHistory([
          { date: "Sep 1", price: 12500 },
          { date: "Sep 5", price: 12000 },
          { date: "Sep 10", price: 11800 },
          { date: "Sep 15", price: 11500 },
          { date: "Sep 20", price: 11200 },
          { date: "Sep 25", price: 11000 },
          { date: "Sep 30", price: 10800 },
        ]);
      } finally {
        setLoading(false);
      }
    };

    if (productId) {
      fetchPriceHistory();
    }
  }, [productId]);

  if (loading) {
    return (
      <div className="price-history-card">
        <h3>Price History</h3>

        <p className="price-history-message">
          Loading price history...
        </p>
      </div>
    );
  }

  if (priceHistory.length < 2) {
    return (
      <div className="price-history-card">
        <h3>Price History</h3>

        <p className="price-history-message">
          Not enough price history yet.
        </p>
      </div>
    );
  }

  return (
    <div className="price-history-card">
      <div className="price-history-header">
        <h3>Price History</h3>

        <p>
          Track how the product price has changed over time.
        </p>
      </div>

      <div className="price-history-chart">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={priceHistory}
            margin={{
              top: 10,
              right: 20,
              left: 10,
              bottom: 10,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="date" />

            <YAxis />

            <Tooltip
              formatter={(value) => [`৳${value}`, "Price"]}
            />

            <Line
              type="monotone"
              dataKey="price"
              stroke="#8B7BC8"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PriceHistoryChart;