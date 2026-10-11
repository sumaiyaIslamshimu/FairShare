import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { loginUser } from "../api/authApi";
import { validateLoginForm } from "../utils/validation";
import "./Login.css";

const INITIAL_FORM = {
  email: "",
  password: "",
  rememberMe: false,
};

function Login() {
  const navigate = useNavigate();

  const [form, setForm] = useState(INITIAL_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  function handleChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setServerError("");

    // Figma labels this field "Email or Username", but the backend
    // only supports email + password, so it's always validated/sent as email.
    const errors = validateLoginForm({ email: form.email, password: form.password });
    setFieldErrors(errors);

    if (Object.keys(errors).length > 0) {
      return; // Invalid data must never be sent to the backend.
    }

    setIsSubmitting(true);
    try {
      const data = await loginUser({
        email: form.email.trim(),
        password: form.password,
      });

      localStorage.setItem("access_token", data.access_token);

      navigate("/");
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
            <h1 className="auth-title">Welcome back</h1>
            <p className="auth-subtitle">Sign in to your shopper account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          {serverError && <div className="server-error">{serverError}</div>}

          <label className="field-label" htmlFor="email">
            Email or Username
          </label>
          <div className="input-wrapper">
            <span className="input-icon">✉️</span>
            <input
              id="email"
              type="text"
              placeholder="you@example.com"
              value={form.email}
              onChange={(e) => handleChange("email", e.target.value)}
              className={fieldErrors.email ? "input-error" : ""}
            />
          </div>
          {fieldErrors.email && <p className="error-text">{fieldErrors.email}</p>}

          <label className="field-label" htmlFor="password">
            Password
          </label>
          <div className="input-wrapper">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
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

          <div className="login-options-row">
            <label className="remember-me">
              <input
                type="checkbox"
                checked={form.rememberMe}
                onChange={(e) => handleChange("rememberMe", e.target.checked)}
              />
              Remember me
            </label>
            <a href="#forgot-password" className="forgot-link">
              Forgot password?
            </a>
          </div>

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "Signing In..." : "User Login"}
          </button>
        </form>

        <hr className="divider" />

        <p className="switch-auth-text">
          Don&apos;t have an account? <Link to="/register">Create User Account</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;