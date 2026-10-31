import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getSellerProduct } from "../../api/shopping.js";
import { request } from "../../api/client.js";
import { useCart } from "../../context/CartContext.jsx";
import Button from "../../components/Button.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import "../../styles/shopping.css";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refresh } = useCart();

  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isAdding, setIsAdding] = useState(false);
  const [isBuying, setIsBuying] = useState(false);
  const [cartError, setCartError] = useState(null);
  const [notice, setNotice] = useState(null);

  useEffect(() => {
    getSellerProduct(id)
      .then(setProduct)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [id]);

  // Reusable helper to send the exact payload FastAPI needs
  const addToBackendCart = async () => {
    await request('/cart/items', {
      method: "POST",
      body: {
        product_id: id,
        seller_product_id: id,
        source: "fairshare",
        quantity: 1
      }
    });
    // Force the frontend cart context to sync with the new database cart
    await refresh();
  };

  const handleAddToCart = async () => {
    setCartError(null);
    setNotice(null);
    setIsAdding(true);
    try {
      await addToBackendCart();
      setNotice("Added to cart successfully!");
    } catch (err) {
      setCartError(err);
    } finally {
      setIsAdding(false);
    }
  };

  const handleBuyNow = async () => {
    setCartError(null);
    setNotice(null);
    setIsBuying(true);
    try {
      await addToBackendCart();
      // Instantly jump to the cart page so the user can enter their shipping address
      navigate('/app/cart');
    } catch (err) {
      setCartError(err);
      setIsBuying(false); // Only reset if it fails, otherwise let it navigate
    }
  };

  if (loading) return <div>Loading product details...</div>;
  if (error) return <ErrorBox error={error} />;
  if (!product) return <div>Product not found.</div>;

  return (
    <div className="product-detail fade-in-up">
      <Button variant="secondary" onClick={() => navigate(-1)} style={{ marginBottom: "1rem" }}>
        &larr; Back
      </Button>

      <div className="detail-card" style={{ display: "flex", gap: "2rem", flexWrap: "wrap", background: "#fff", padding: "2rem", borderRadius: "8px", border: "1px solid #eee" }}>

        {/* Image Display */}
        <div className="image-container" style={{ flex: "1 1 300px", maxWidth: "400px" }}>
          {product.image_url || (product.images && product.images.length > 0) ? (
            <img
              src={product.image_url || product.images[0]}
              alt={product.name}
              style={{ width: "100%", borderRadius: "8px", objectFit: "contain", maxHeight: "400px" }}
            />
          ) : (
            <div style={{ width: "100%", height: "300px", background: "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "8px" }}>
              No Image Available
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="info-container" style={{ flex: "2 1 400px" }}>
          <h1 style={{ margin: "0 0 0.5rem 0" }}>{product.name}</h1>
          <p style={{ color: "#666", marginBottom: "1.5rem" }}>
            Sold by: <strong>{product.seller_name || "FairShare Seller"}</strong>
          </p>

          <h2 style={{ color: "var(--primary)", fontSize: "1.8rem", marginBottom: "1rem" }}>
            {product.currency} {product.price_paisa / 100}
          </h2>

          <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
            <span style={{ padding: "0.25rem 0.75rem", background: "var(--green-light, #d1fae5)", color: "var(--green-dark, #065f46)", borderRadius: "20px", fontSize: "0.9rem" }}>
              {product.availability === "in_stock" ? "In Stock" : "Unavailable"}
            </span>
            {product.unit && (
              <span style={{ padding: "0.25rem 0.75rem", background: "#f3f4f6", color: "#4b5563", borderRadius: "20px", fontSize: "0.9rem" }}>
                Unit: {product.unit}
              </span>
            )}
          </div>

          <p style={{ lineHeight: "1.6", color: "#4b5563", marginBottom: "2rem" }}>
            {product.description || "No description available for this product."}
          </p>

          <ErrorBox error={cartError} />
          {notice && <div style={{ color: "var(--green-dark)", background: "var(--green-light)", padding: "0.75rem", borderRadius: "4px", marginBottom: "1rem" }}>{notice}</div>}

          {/* Side-by-Side Action Buttons */}
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            <Button
              variant="primary"
              onClick={handleBuyNow}
              disabled={isAdding || isBuying || product.availability !== "in_stock"}
              style={{
                padding: "0.75rem 2rem",
                fontSize: "1.1rem",
                background: "#f97316", // A distinct orange color for Buy Now
                color: "#fff",
                border: "none",
                flex: "1 1 auto"
              }}
            >
              {isBuying ? "Processing..." : "Buy Now"}
            </Button>

            <Button
              variant="primary"
              onClick={handleAddToCart}
              disabled={isAdding || isBuying || product.availability !== "in_stock"}
              style={{
                padding: "0.75rem 2rem",
                fontSize: "1.1rem",
                flex: "1 1 auto"
              }}
            >
              {isAdding ? "Adding..." : "Add to Cart"}
            </Button>
          </div>

        </div>
      </div>
    </div>
  );
}