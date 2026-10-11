import { useState, useEffect } from "react";
import ProductCard from "./ProductCard";
import "./RecommendationsSection.css";

const API_BASE = "http://127.0.0.1:8000";

const SAMPLE_ALTERNATIVES = [
  {
    _id: "a1",
    name: "Anker Soundcore Q45",
    brand: "Anker",
    category: "Electronics",
    price: 79,
    rating: 4.5,
    marketplace_name: "Anker",
    in_stock: true,
    is_verified: true,
    image_url:
      "https://placehold.co/400x300/f3f4f6/a1a1aa?text=Anker+Q45",
  },
  {
    _id: "a2",
    name: "JBL Tune 760NC",
    brand: "JBL",
    category: "Electronics",
    price: 69,
    rating: 4.3,
    marketplace_name: "JBL",
    in_stock: true,
    is_verified: true,
    image_url:
      "https://placehold.co/400x300/f3f4f6/a1a1aa?text=JBL+760NC",
  },
  {
    _id: "a3",
    name: "Sony WH-CH720N",
    brand: "Sony",
    category: "Electronics",
    price: 99,
    rating: 4.4,
    marketplace_name: "Sony",
    in_stock: true,
    is_verified: true,
    image_url:
      "https://placehold.co/400x300/f3f4f6/a1a1aa?text=Sony+CH720N",
  },
  {
    _id: "a4",
    name: "Boat Rockerz 450",
    brand: "Boat",
    category: "Electronics",
    price: 45,
    rating: 4.1,
    marketplace_name: "Boat",
    in_stock: true,
    is_verified: false,
    image_url:
      "https://placehold.co/400x300/f3f4f6/a1a1aa?text=Boat+450",
  },
];

function RecommendationsSection({ productId, budget, currentPrice }) {
  const [alternatives, setAlternatives] = useState([]);
  const [loading, setLoading] = useState(false);

  const isOverBudget =
    budget != null &&
    currentPrice != null &&
    currentPrice > budget;

  useEffect(() => {
    if (!isOverBudget) {
      setAlternatives([]);
      return;
    }

    setLoading(true);

    fetch(
      `${API_BASE}/products/recommendations?productId=${productId}&budget=${budget}`
    )
      .then((res) => {
        if (!res.ok) {
          throw new Error("No recommendation endpoint yet");
        }

        return res.json();
      })
      .then((data) => {
        setAlternatives(data);
      })
      .catch(() => {
        setAlternatives(
          SAMPLE_ALTERNATIVES.filter(
            (product) => product.price <= budget
          )
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, [productId, budget, isOverBudget]);

  if (!isOverBudget) {
    return null;
  }

  return (
    <div className="recommendations-section">
      <p className="recommendations-note">
        This product is over your budget of ৳{budget.toLocaleString()}.
        Here are options within it.
      </p>

      {loading && (
        <p className="status-text">
          Loading alternatives...
        </p>
      )}

      {!loading && alternatives.length === 0 && (
        <p className="status-text">
          No alternatives found within your budget.
        </p>
      )}

      {!loading && alternatives.length > 0 && (
        <div className="recommendations-grid">
          {alternatives.slice(0, 4).map((product) => (
            <ProductCard
              key={product._id || product.id}
              product={product}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default RecommendationsSection;