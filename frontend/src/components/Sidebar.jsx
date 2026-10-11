import { useState, useEffect } from 'react';

const navigationItems = [
  { label: 'Home', icon: '⌂' },
  { label: 'Search & Browse', icon: '⌕' },
  { label: 'Create Listing', icon: '⊕' }, // Added for SCRUM-188
  { label: 'Rental Requests', icon: '✉' }, // Added for SCRUM-190
  { label: 'Compare', icon: '↔' },
  { label: 'Recommendations', icon: '✧' },
  { label: 'Price Tracking', icon: '↗' },
  { label: 'Rentals', icon: '♙' },
  { label: 'Messages', icon: '▱' },
  { label: 'Notifications', icon: '♟' },
  { label: 'Profile', icon: '♙' },
];

function Sidebar() {
  const [currentHash, setCurrentHash] = useState(window.location.hash || '#search-&-browse');

  useEffect(() => {
    const handleHashChange = () => setCurrentHash(window.location.hash);
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return (
    <aside className="sidebar">
      <nav className="sidebar-navigation" aria-label="Main navigation">
        {navigationItems.map((item) => {
          const itemHash = `#${item.label.toLowerCase().replaceAll(' ', '-')}`;
          const isActive = currentHash === itemHash || (currentHash === '' && item.label === 'Search & Browse');
          
          return (
            <a
              className={`navigation-link${isActive ? ' active' : ''}`}
              href={itemHash}
              aria-current={isActive ? 'page' : undefined}
              key={item.label}
            >
              <span className="navigation-icon" aria-hidden="true">{item.icon}</span>
              {item.label}
            </a>
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