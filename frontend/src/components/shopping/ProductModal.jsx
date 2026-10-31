import React from "react";
import Button from "../Button.jsx";

export default function ProductModal({ item, onClose }) {
  if (!item) return null;

  // Dynamically generate a fallback search URL just in case the main link is dead
  const getFallbackUrl = () => {
    const query = encodeURIComponent(item.name.trim());
    if (item.store === "shwapno") return `https://www.shwapno.com/search?q=${query}`;
    if (item.store === "chaldal") return `https://chaldal.com/search/${query}`;
    return null;
  };

  const fallbackUrl = getFallbackUrl();

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Close Button */}
        <button className="modal-close-btn" onClick={onClose}>
          &times;
        </button>

        {/* Left Side: Large Product Image */}
        <div style={{ flex: "1", background: "#f8f9fa", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", minHeight: "300px" }}>
          <img
            src={item.image_url || "https://via.placeholder.com/300"}
            alt={item.name}
            style={{ maxWidth: "100%", maxHeight: "280px", objectFit: "contain", borderRadius: "8px" }}
          />
        </div>

        {/* Right Side: Details & Actions */}
        <div style={{ flex: "1.2", padding: "2.5rem 2rem 2rem 2rem", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: "0.85rem", color: "#666", textTransform: "uppercase", marginBottom: "0.3rem", fontWeight: "600" }}>
              {item.store_name} {item.brand ? `• ${item.brand}` : ""}
            </div>
            <h2 style={{ fontSize: "1.5rem", color: "#222", marginBottom: "0.5rem", lineHeight: "1.3" }}>
              {item.name}
            </h2>
            <div style={{ fontSize: "0.9rem", color: "#888", marginBottom: "1.5rem" }}>
              Size / Unit: {item.quantity || 1} {item.unit || "pcs"}
            </div>

            <div style={{ fontSize: "1.8rem", fontWeight: "700", color: "#2c3e50", marginBottom: "1.5rem" }}>
              {item.currency || "৳"} {item.price_paisa ? (item.price_paisa / 100).toLocaleString() : "0"}
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem", width: "100%" }}>
            {item.store_url ? (
              <>
                <a href={item.store_url} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
                  <Button variant="primary" style={{ width: "100%" }}>
                    View at {item.store_name}
                  </Button>
                </a>

                {/* The Smart Fallback Button (Only shows for Shwapno & Chaldal) */}
                {fallbackUrl && (
                  <a href={fallbackUrl} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
                    <button
                      style={{
                        width: "100%",
                        padding: "0.5rem",
                        background: "transparent",
                        border: "1px solid #ddd",
                        borderRadius: "6px",
                        color: "#666",
                        cursor: "pointer",
                        fontSize: "0.85rem",
                        transition: "background 0.2s"
                      }}
                      onMouseOver={(e) => e.target.style.background = "#f0f2f5"}
                      onMouseOut={(e) => e.target.style.background = "transparent"}
                    >
                      Link broken? Search item instead
                    </button>
                  </a>
                )}
              </>
            ) : (
              <Button variant="primary" style={{ width: "100%" }}>
                Add to Cart
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}