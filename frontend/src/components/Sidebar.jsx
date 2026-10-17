import { Link, NavLink } from "react-router-dom";

export default function Sidebar({ portalLabel, items, onSignOut }) {
  return (
    <aside className="sidebar">
      <Link to="/" className="logo brand">
        <span className="logo-mark">F</span>
        <span>
          FairShare
          <small>{portalLabel}</small>
        </span>
      </Link>
      <nav>
        {items.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <button className="signout" onClick={onSignOut}>Sign out</button>
    </aside>
  );
}