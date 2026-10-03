import { Link } from "react-router-dom";
import "./ExperienceSelection.css";

function ExperienceSelection() {
  return (
    <div className="experience-page">
      <nav className="experience-navbar">
        <div className="experience-brand">
          <span className="experience-logo-icon">🛍️</span>
          <span className="experience-logo">FairShare</span>
        </div>
        <div className="experience-nav-actions">
          <Link to="/login" className="role-button role-button-outline">
            Sign In
          </Link>
          <Link to="/register" className="role-button role-button-dark">
            Get Started
          </Link>
        </div>
      </nav>

      <div className="experience-hero">
        <h1 className="experience-title">Choose Your Experience</h1>
        <p className="experience-subtitle">
          Select how you'd like to use FairShare. Shoppers, sellers, and
          administrators each get a tailored experience built for their needs.
        </p>
      </div>

      <div className="role-grid">
        <div className="role-card">
          <div className="role-card-body">
            <div className="role-icon">👤</div>
            <h2 className="role-title">User / Shopper</h2>
            <p className="role-description">
              Compare products, prices, ratings, and reviews across sellers to
              make better, more informed buying decisions on FairShare.
            </p>
          </div>
          <div className="role-actions">
            <Link to="/login" className="role-button role-button-dark">
              User Login
            </Link>
            <Link to="/register" className="role-button role-button-outline">
              User Registration
            </Link>
          </div>
        </div>

        <div className="role-card">
          <div className="role-card-body">
            <div className="role-icon">🏬</div>
            <h2 className="role-title">Seller</h2>
            <p className="role-description">
              Manage your products, pricing, and listings, and interact
              directly with customers browsing the FairShare marketplace.
            </p>
          </div>
          <div className="role-actions">
            <button type="button" className="role-button role-button-dark">
              Seller Login
            </button>
            <button type="button" className="role-button role-button-outline">
              Seller Registration
            </button>
          </div>
        </div>

        <div className="role-card">
          <div className="role-card-body">
            <div className="role-icon">🛡️</div>
            <h2 className="role-title">Admin</h2>
            <p className="role-description">
              Manage and monitor the FairShare platform, including users,
              sellers, listings, and overall marketplace integrity.
            </p>
          </div>
          <div className="role-actions">
            <button
              type="button"
              className="role-button role-button-restricted"
              disabled
            >
              🔒 Restricted
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ExperienceSelection;