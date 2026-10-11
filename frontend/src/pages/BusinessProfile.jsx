import { useState, useEffect } from "react";
import { validateBusinessProfile } from "../utils/validation";
import "./BusinessProfile.css";

const API_BASE = "http://127.0.0.1:8000";

function BusinessProfile() {
  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [errors, setErrors] = useState({});

  useEffect(() => {
    fetch(`${API_BASE}/seller/profile`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load profile");
        return res.json();
      })
      .then((data) => {
        setProfile(data);
        setFormData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    const validationErrors = validateBusinessProfile(formData);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/seller/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to save changes");
      }
      const updated = await res.json();
      setProfile(updated);
      setFormData(updated);
      setIsEditing(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData(profile);
    setErrors({});
    setIsEditing(false);
  };

  if (loading) return <p className="status-text">Loading profile...</p>;
  if (error && !profile) return <p className="status-text error">{error}</p>;

  const initials = profile.businessName
    ? profile.businessName
        .split(" ")
        .map((w) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "?";

  // Single source of truth for both view and edit mode — keeps layout identical
  const fields = [
    { key: "businessName", label: "Business Name", type: "text" },
    { key: "ownerName", label: "Owner Name", type: "text" },
    { key: "email", label: "Business Email", type: "email" },
    { key: "contactNumber", label: "Phone Number", type: "text" },
    { key: "businessCategory", label: "Business Category", type: "text" },
    { key: "website", label: "Website (optional)", type: "text" },
  ];

  return (
    <div className="seller-shell">
      <aside className="sidebar">
        <div className="sidebar-logo brand-logo">
          <span className="logo-icon">🛍️</span>
          <div>
            <div className="logo-text">FairShare</div>
            <div className="logo-sub">Seller Portal</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <a href="/seller/dashboard" className="nav-item">▦ Dashboard</a>
          <a href="/seller/profile" className="nav-item active">👤 Business Profile</a>
          <a href="/seller/products" className="nav-item">📦 Products</a>
          <a href="/seller/inventory" className="nav-item">🧰 Inventory</a>
          <a href="/seller/pricing" className="nav-item">$ Pricing</a>
          <a href="/seller/competitive-pricing" className="nav-item">📈 Competitive Pricing</a>
          <a href="/seller/promotions" className="nav-item">🏷️ Promotions</a>
          <a href="/seller/spotlight" className="nav-item">⭐ Seller Spotlight</a>
          <a href="/seller/messages" className="nav-item">💬 Messages</a>
          <a href="/seller/verification" className="nav-item">🛡️ Verification</a>
          <a href="/seller/settings" className="nav-item">⚙️ Settings</a>
        </nav>

        <a href="/logout" className="sign-out">↩ Sign Out</a>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <span className="store-name">{profile.businessName}</span>
          <div className="topbar-right">
            <span className="verified-badge">Verified Seller</span>
            <span className="icon-btn">🔔</span>
            <div className="avatar-chip">MC</div>
            <div>
              <div className="user-name">Marcus Chen</div>
              <div className="user-role">Owner</div>
            </div>
          </div>
        </header>

        <main className="content">
          <div className="profile-card">
            <div className="profile-card-header">
              <div className="store-avatar">{initials}</div>
              <div>
                <div className="store-title-row">
                  <h1>{profile.businessName}</h1>
                  <span className="shield-icon">🛡️</span>
                </div>
                <span className="verified-pill">Verified Seller</span>
                <p className="member-since">
                  Member since March 2023 · Electronics &amp; Accessories
                </p>
              </div>
            </div>

            {error && <p className="status-text error">{error}</p>}

            <div className="field-grid">
              {fields.map(({ key, label, type }) => (
                <div className="form-group" key={key}>
                  <label>{label}</label>
                  {isEditing ? (
                    <input
                      type={type}
                      name={key}
                      value={formData[key] || ""}
                      onChange={handleChange}
                    />
                  ) : (
                    <div className="field-value">
                      {profile[key] || <span className="field-empty">—</span>}
                    </div>
                  )}
                  {isEditing && errors[key] && (
                    <p className="field-error">{errors[key]}</p>
                  )}
                </div>
              ))}

              <div className="form-group span-2">
                <label>Business Description</label>
                {isEditing ? (
                  <textarea
                    name="description"
                    rows={3}
                    value={formData.description || ""}
                    onChange={handleChange}
                  />
                ) : (
                  <div className="field-value field-value-box">
                    {profile.description}
                  </div>
                )}
                {isEditing && errors.description && (
                  <p className="field-error">{errors.description}</p>
                )}
              </div>
            </div>

            <div className="card-actions">
              {isEditing ? (
                <>
                  <button className="btn-secondary" onClick={handleCancel}>
                    Cancel
                  </button>
                  <button
                    className="btn-primary"
                    onClick={handleSave}
                    disabled={saving}
                  >
                    {saving ? "Saving..." : "Save changes"}
                  </button>
                </>
              ) : (
                <button className="btn-primary" onClick={() => setIsEditing(true)}>
                  Edit
                </button>
              )}
            </div>
          </div>

          <div className="stats-card">
            <h2>Store Performance</h2>
            <div className="stats-row">
              <div className="stat-box">
                <div className="stat-number">47</div>
                <div className="stat-label">Products Listed</div>
              </div>
              <div className="stat-box">
                <div className="stat-number">4.8 ★</div>
                <div className="stat-label">Avg. Rating</div>
              </div>
              <div className="stat-box">
                <div className="stat-number">1,240</div>
                <div className="stat-label">Total Reviews</div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default BusinessProfile;