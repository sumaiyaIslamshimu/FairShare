import { Link, useLocation } from 'react-router-dom';

const navigationItems = [
  { label: 'Home', icon: '⌂', path: '/' },
  { label: 'Search & Browse', icon: '⌕', path: '/products' },
  { label: 'Create Listing', icon: '⊕', path: '/seller/listing/new' },
  { label: 'Rental Requests', icon: '✉', path: '/seller/requests' },
  { label: 'Profile', icon: '♙', path: '/seller/profile' },
  // Placeholders for future pages
  { label: 'Compare', icon: '↔', path: '/compare' },
  { label: 'Recommendations', icon: '✧', path: '/recommendations' },
  { label: 'Price Tracking', icon: '↗', path: '/price-tracking' },
  { label: 'Rentals', icon: '♙', path: '/rentals' },
  { label: 'Messages', icon: '▱', path: '/messages' },
  { label: 'Notifications', icon: '♟', path: '/notifications' },
];

function Sidebar() {
  const location = useLocation(); // Gets current route path to highlight active menu item

  return (
    <aside className="sidebar">
      <nav className="sidebar-navigation" aria-label="Main navigation">
        {navigationItems.map((item) => {
          const isActive = location.pathname === item.path;

          return (
            <Link
              className={`navigation-link${isActive ? ' active' : ''}`}
              to={item.path}
              aria-current={isActive ? 'page' : undefined}
              key={item.label}
            >
              <span className="navigation-icon" aria-hidden="true">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <button className="sign-out-button" type="button" disabled>
        <span aria-hidden="true">↪</span>
        Sign Out
      </button>
    </aside>
  );
}

export default Sidebar;