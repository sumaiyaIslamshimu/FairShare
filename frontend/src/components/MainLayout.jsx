import { useCallback, useState } from 'react';
import Sidebar from './Sidebar';

function MainLayout({ children }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const syncSearchQuery = useCallback((query) => setSearchQuery(query), []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <button
            className="menu-toggle"
            type="button"
            aria-label={sidebarOpen ? 'Hide navigation' : 'Show navigation'}
            aria-expanded={sidebarOpen}
            onClick={() => setSidebarOpen((open) => !open)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="brand-mark" aria-hidden="true">
            <span />
          </div>
          <div className="brand-copy">
            <strong>FairShare</strong>
            <span>Shopper</span>
          </div>
        </div>

        <label className="topbar-search">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="10.8" cy="10.8" r="6.8" />
            <path d="m16 16 4.5 4.5" />
          </svg>
          <span className="visually-hidden">Search products and brands</span>
          <input
            placeholder="Search products, brands..."
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
        </label>

        <div className="account-controls">
          <button className="notification-button" type="button" aria-label="Notifications">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9m-8 12h4" />
            </svg>
            <span />
          </button>
          <button className="profile-button" type="button">
            <span className="avatar">AJ</span>
            <span className="profile-copy">
              <strong>Alex Johnson</strong>
              <span>Shopper</span>
            </span>
            <span className="profile-chevron" aria-hidden="true">⌄</span>
          </button>
        </div>
      </header>
      <div className="app-body">
        {sidebarOpen && <Sidebar />}
        <div className="page-content">
          {typeof children === 'function' ? children(syncSearchQuery) : children}
        </div>
      </div>
    </div>
  );
}

export default MainLayout;
