
import { Link, NavLink } from "react-router-dom";
import BrandLogo from "./BrandLogo.jsx";

const ICONS = {
  // User
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

  // Seller
  "My Products": "📦",
  "Business Profile": "👤",
  Insights: "📈",
  Promotions: "✨",
  Orders: "📦",
  "My Rentals": "🏠",
  Reviews: "⭐",
  Returns: "↩️",

  // Admin
  Dashboard: "📊",
  "Verification & Sellers": "✓",
  "Listing Moderation": "📋",
  Categories: "☷",
  Complaints: "⚠️",
  "Scraping Monitor": "🔄",
  "Audit Log": "📋",
  "Review Moderation": "⭐",
  Returns: "↩️",
  Notifications: "🔔",
};


export default function Sidebar({ portalLabel, items, onSignOut }) {
  return (
    <aside className="sidebar">
      <BrandLogo
  showPortal
  portalLabel={portalLabel}
/>

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

            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <button className="signout" onClick={onSignOut}>
        Sign out
      </button>
    </aside>
  );
}
