import { NavLink } from "react-router-dom";
import BrandLogo from "./BrandLogo.jsx";
import { useCart } from "../context/CartContext.jsx";

// Cleaned up object with all duplicates removed
const ICONS = {
  Home: "🏠",
  "Search & Compare": "🔍",
  Cart: "🛒",
  "My Orders": "📦",
  Rentals: "🏠",
  Messages: "💬",
  Verification: "✓",
  Complaints: "⚠️",
  "My Reviews": "⭐",
  "My Returns": "↩️",
  "Price Watch": "📈",
  Notifications: "🔔",
  "My Products": "📦",
  "Business Profile": "👤",
  Insights: "📈",
  Promotions: "✨",
  Orders: "📦",
  "My Rentals": "🏠",
  Reviews: "⭐",
  Returns: "↩️",
  Dashboard: "📊",
  "Verification & Sellers": "✓",
  "Listing Moderation": "📋",
  Categories: "☷",
  "Scraping Monitor": "🔄",
  "Audit Log": "📋",
  "Review Moderation": "⭐",
};

// Helper component that ONLY calls useCart when rendering the "Cart" link
function CartBadge({ label }) {
  const { cart } = useCart();
  const cartItemCount = cart?.total_items || cart?.items?.length || 0;

  return (
    <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
      {label}
      {cartItemCount > 0 && (
        <span
          style={{
            background: "#ef4444",
            color: "white",
            borderRadius: "12px",
            padding: "2px 8px",
            fontSize: "0.8rem",
            fontWeight: "bold",
            lineHeight: "1",
          }}
        >
          {cartItemCount}
        </span>
      )}
    </span>
  );
}

// Helper to decide if we need the badge or just standard text
function NavLabel({ label }) {
  if (label === "Cart") return <CartBadge label={label} />;
  return <span>{label}</span>;
}

export default function Sidebar({ portalLabel, items, onSignOut }) {
  return (
    <aside className="sidebar">
      <BrandLogo showPortal portalLabel={portalLabel} />

      <nav>
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `nav-link ${isActive ? "active" : ""}`
            }
          >
            <span className="nav-icon" aria-hidden="true">
              {ICONS[item.label] || "•"}
            </span>

            {/* Render the label through our smart helper */}
            <NavLabel label={item.label} />
          </NavLink>
        ))}
      </nav>

      <button className="signout" onClick={onSignOut}>
        Sign out
      </button>
    </aside>
  );
}