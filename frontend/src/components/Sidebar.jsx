const navigationItems = [
  { label: 'Home', icon: '⌂' },
  { label: 'Search & Browse', icon: '⌕', active: true },
  { label: 'Compare', icon: '↔' },
  { label: 'Recommendations', icon: '✧' },
  { label: 'Price Tracking', icon: '↗' },
  { label: 'Rentals', icon: '♙' },
  { label: 'Messages', icon: '▱' },
  { label: 'Notifications', icon: '♟' },
  { label: 'Profile', icon: '♙' },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <nav className="sidebar-navigation" aria-label="Main navigation">
        {navigationItems.map((item) => (
          <a
            className={`navigation-link${item.active ? ' active' : ''}`}
            href={item.active ? '/' : `#${item.label.toLowerCase().replaceAll(' ', '-')}`}
            aria-current={item.active ? 'page' : undefined}
            key={item.label}
          >
            <span className="navigation-icon" aria-hidden="true">{item.icon}</span>
            {item.label}
          </a>
        ))}
      </nav>
      <button className="sign-out-button" type="button" disabled>
        <span aria-hidden="true">↪</span>
        Sign Out
      </button>
    </aside>
  );
}

export default Sidebar;
