import "./ShopperLayout.css";

function ShopperLayout({ activePage, pageTitle, children }) {
  const navItems = [
    { key: "home", label: "🏠 Home", href: "/shopper/home" },
    { key: "search", label: "🔍 Search & Browse", href: "/shopper/search" },
    { key: "compare", label: "⇄ Compare", href: "/shopper/compare" },
    {
      key: "recommendations",
      label: "✨ Recommendations",
      href: "/shopper/recommendations",
    },
    {
      key: "price-tracking",
      label: "📈 Price Tracking",
      href: "/shopper/price-tracking",
    },
    { key: "rentals", label: "🏠 Rentals", href: "/shopper/rentals" },
    { key: "messages", label: "💬 Messages", href: "/shopper/messages" },
    {
      key: "notifications",
      label: "🔔 Notifications",
      href: "/shopper/notifications",
    },
    { key: "profile", label: "👤 Profile", href: "/shopper/profile" },
  ];

  return (
    <div className="shopper-shell">
      <aside className="sidebar">
        <div className="sidebar-logo brand-logo">
          <span className="logo-icon">🛍️</span>

          <div>
            <div className="logo-text">FairShare</div>
            <div className="logo-sub">Shopper</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <a
              key={item.key}
              href={item.href}
              className={`nav-item ${
                activePage === item.key ? "active" : ""
              }`}
            >
              {item.label}
            </a>
          ))}
        </nav>

        <a href="/logout" className="sign-out">
          ↩ Sign Out
        </a>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <span className="page-title">{pageTitle}</span>

          <div className="topbar-right">
            <span className="icon-btn">🔔</span>

            <div className="avatar-chip">AJ</div>

            <div>
              <div className="user-name">Alex Johnson</div>
              <div className="user-role">Shopper</div>
            </div>
          </div>
        </header>

        <main className="content">{children}</main>
      </div>
    </div>
  );
}

export default ShopperLayout;