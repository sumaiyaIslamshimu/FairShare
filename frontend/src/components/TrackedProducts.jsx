import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import "./TrackedProducts.css";

const API_BASE = "http://127.0.0.1:8000";

const TrackedProducts = () => {
  const [trackedProducts, setTrackedProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchTrackedProducts = async () => {
      const token = localStorage.getItem("fairshare_token");

      if (!token) {
        navigate("/shopper/login");
        return;
      }

      try {
        setLoading(true);

        const response = await fetch(
          `${API_BASE}/shopper/tracked-products`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error("Failed to fetch tracked products");
        }

        const data = await response.json();

        setTrackedProducts(data);
      } catch (error) {
        console.error("Error fetching tracked products:", error);

        // Temporary sample data until backend endpoint is connected
        setTrackedProducts([
          {
            id: "1",
            name: "Sony WH-1000XM5",
            image:
              "https://via.placeholder.com/120",
            currentPrice: 32000,
            targetPrice: 30000,
            marketplace: "Daraz",
          },
          {
            id: "2",
            name: "Apple AirPods Pro",
            image:
              "https://via.placeholder.com/120",
            currentPrice: 24500,
            targetPrice: 22000,
            marketplace: "Pickaboo",
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchTrackedProducts();
  }, [navigate]);

  const handleRemoveTracking = (productId) => {
    setTrackedProducts((previousProducts) =>
      previousProducts.filter((product) => product.id !== productId)
    );
  };

  if (loading) {
    return (
      <div className="tracked-products-page">
        <div className="tracked-products-container">
          <p className="tracked-products-message">
            Loading tracked products...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="tracked-products-page">
      <div className="tracked-products-container">
        <div className="tracked-products-header">
          <div>
            <h1>My Tracked Products</h1>
            <p>
              Keep an eye on products and get notified when prices reach your
              target.
            </p>
          </div>
        </div>

        {trackedProducts.length === 0 ? (
          <div className="tracked-products-empty">
            <h2>No tracked products yet</h2>

            <p>
              Start tracking a product to monitor its price.
            </p>

            <button
              onClick={() => navigate("/shopper/products")}
              className="browse-products-button"
            >
              Browse Products
            </button>
          </div>
        ) : (
          <div className="tracked-products-list">
            {trackedProducts.map((product) => (
              <div
                className="tracked-product-card"
                key={product.id}
              >
                <div className="tracked-product-image">
                  <img
                    src={product.image}
                    alt={product.name}
                  />
                </div>

                <div className="tracked-product-info">
                  <h2>{product.name}</h2>

                  <p className="tracked-marketplace">
                    Marketplace: {product.marketplace}
                  </p>

                  <div className="price-details">
                    <div>
                      <span>Current Price</span>
                      <strong>
                        ৳{product.currentPrice.toLocaleString()}
                      </strong>
                    </div>

                    <div>
                      <span>Target Price</span>
                      <strong>
                        ৳{product.targetPrice.toLocaleString()}
                      </strong>
                    </div>
                  </div>

                  {product.currentPrice <= product.targetPrice && (
                    <p className="target-reached">
                      🎉 Your target price has been reached!
                    </p>
                  )}

                  <div className="tracked-product-actions">
                    <button
                      className="history-button"
                      onClick={() =>
                        navigate(
                          `/shopper/price-history/${product.id}`
                        )
                      }
                    >
                      View Price History
                    </button>

                    <button
                      className="remove-tracking-button"
                      onClick={() =>
                        handleRemoveTracking(product.id)
                      }
                    >
                      Stop Tracking
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TrackedProducts;