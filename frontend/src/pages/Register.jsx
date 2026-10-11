import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../api/authApi";
import { validateRegisterForm } from "../utils/validation";
import "./Register.css";

const INITIAL_FORM = {
  name: "",
  email: "",
  phone: "",
  password: "",
  confirmPassword: "",
  agreedToTerms: false,
};

function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState(INITIAL_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  function handleChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setServerError("");

    const errors = validateRegisterForm(form);
    setFieldErrors(errors);

    if (Object.keys(errors).length > 0) {
      return; // Invalid data must never be sent to the backend.
    }

    setIsSubmitting(true);
    try {
      await registerUser({
        name: form.name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        password: form.password,
      });
      setIsSuccess(true);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      setServerError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <Link to="/" className="back-link">
        &larr; Back to Role Selection
      </Link>

      <div className="auth-card">
        <div className="auth-card-header">
          <div className="auth-icon">🛍️</div>
          <div>
            <h1 className="auth-title">Create Account</h1>
            <p className="auth-subtitle">Join FairShare as a shopper</p>
          </div>
        </div>

        {isSuccess ? (
          <div className="success-banner">
            Account created successfully! Redirecting to login&hellip;
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            {serverError && <div className="server-error">{serverError}</div>}

            <label className="field-label" htmlFor="name">
              Full Name
            </label>
            <div className="input-wrapper">
              <span className="input-icon">👤</span>
              <input
                id="name"
                type="text"
                placeholder="Enter your full name"
                value={form.name}
                onChange={(e) => handleChange("name", e.target.value)}
                className={fieldErrors.name ? "input-error" : ""}
              />
            </div>
            {fieldErrors.name && <p className="error-text">{fieldErrors.name}</p>}

            <label className="field-label" htmlFor="email">
              Email Address
            </label>
            <div className="input-wrapper">
              <span className="input-icon">✉️</span>
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) => handleChange("email", e.target.value)}
                className={fieldErrors.email ? "input-error" : ""}
              />
            </div>
            {fieldErrors.email && <p className="error-text">{fieldErrors.email}</p>}

            <label className="field-label" htmlFor="phone">
              Phone Number
            </label>
            <div className="input-wrapper">
              <span className="input-icon">📞</span>
              <input
                id="phone"
                type="tel"
                placeholder="+880 1XXXXXXXXX"
                value={form.phone}
                onChange={(e) => handleChange("phone", e.target.value)}
                className={fieldErrors.phone ? "input-error" : ""}
              />
            </div>
            {fieldErrors.phone && <p className="error-text">{fieldErrors.phone}</p>}

            <label className="field-label" htmlFor="password">
              Password
            </label>
            <div className="input-wrapper">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Create a strong password"
                value={form.password}
                onChange={(e) => handleChange("password", e.target.value)}
                className={fieldErrors.password ? "input-error" : ""}
              />
              <button
                type="button"
                className="show-toggle"
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            {fieldErrors.password && <p className="error-text">{fieldErrors.password}</p>}

            <label className="field-label" htmlFor="confirmPassword">
              Confirm Password
            </label>
            <div className="input-wrapper">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                placeholder="Repeat your password"
                value={form.confirmPassword}
                onChange={(e) => handleChange("confirmPassword", e.target.value)}
                className={fieldErrors.confirmPassword ? "input-error" : ""}
              />
              <button
                type="button"
                className="show-toggle"
                onClick={() => setShowConfirmPassword((v) => !v)}
              >
                {showConfirmPassword ? "Hide" : "Show"}
              </button>
            </div>
            {fieldErrors.confirmPassword && (
              <p className="error-text">{fieldErrors.confirmPassword}</p>
            )}

            <div className="terms-row">
              <input
                id="agreedToTerms"
                type="checkbox"
                checked={form.agreedToTerms}
                onChange={(e) => handleChange("agreedToTerms", e.target.checked)}
              />
              <label htmlFor="agreedToTerms">
                I agree to the <a href="#terms">Terms &amp; Conditions</a> and{" "}
                <a href="#privacy">Privacy Policy</a>
              </label>
            </div>
            {fieldErrors.agreedToTerms && (
              <p className="error-text">{fieldErrors.agreedToTerms}</p>
            )}

            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "Creating Account..." : "Create User Account"}
            </button>
          </form>
        )}

        <p className="switch-auth-text">
          Already have an account? <Link to="/login">Sign In</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;