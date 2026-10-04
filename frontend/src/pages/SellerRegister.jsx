import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { validateSellerRegistration } from "../utils/validation";
import "./SellerRegister.css";

const API_BASE = "http://127.0.0.1:8000";

function SellerRegister() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    businessName: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateSellerRegistration(formData);
    setErrors(validationErrors);
    setServerError("");

    if (Object.keys(validationErrors).length > 0) return;

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/seller/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Registration failed.");
      }
      navigate("/seller/login");
    } catch (err) {
      setServerError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="brand-logo auth-brand">
          <span className="logo-icon">🛍️</span>
          <div>
            <div className="logo-text">Create Seller Account</div>
            <div className="logo-sub">Set up your store on FairShare</div>
          </div>
        </div>

        {serverError && <p className="field-error server-error">{serverError}</p>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="name">Owner Name</label>
              <input
                type="text"
                id="name"
                name="name"
                placeholder="Marcus Chen"
                value={formData.name}
                onChange={handleChange}
              />
              {errors.name && <p className="field-error">{errors.name}</p>}
            </div>

            <div className="form-group">
              <label htmlFor="businessName">Business Name</label>
              <input
                type="text"
                id="businessName"
                name="businessName"
                placeholder="TechVision Store"
                value={formData.businessName}
                onChange={handleChange}
              />
              {errors.businessName && (
                <p className="field-error">{errors.businessName}</p>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Business Email</label>
            <input
              type="email"
              id="email"
              name="email"
              placeholder="marcus@techvision.com"
              value={formData.email}
              onChange={handleChange}
            />
            {errors.email && <p className="field-error">{errors.email}</p>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                placeholder="Create password"
                value={formData.password}
                onChange={handleChange}
              />
              {errors.password && <p className="field-error">{errors.password}</p>}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                placeholder="Repeat password"
                value={formData.confirmPassword}
                onChange={handleChange}
              />
              {errors.confirmPassword && (
                <p className="field-error">{errors.confirmPassword}</p>
              )}
            </div>
          </div>

          <button type="submit" className="btn-primary full-width" disabled={submitting}>
            {submitting ? "Creating account..." : "Create Seller Account"}
          </button>
        </form>

        <p className="auth-footer">
          Already a seller? <Link to="/seller/login">Seller Sign In</Link>
        </p>
      </div>
    </div>
  );
}

export default SellerRegister;