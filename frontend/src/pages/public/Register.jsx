import { useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { HOME_PATH } from "../../navConfig.js";

export default function Register() {
  const { role } = useParams();
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", password: "", confirm: "", business_name: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  if (role !== "user" && role !== "seller") return <Navigate to="/roles" replace />;
  const isSeller = role === "seller";
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  function validate() {
    const e = {};
    if (form.full_name.trim().length < 2) e.full_name = "Enter your full name.";
    if (!/^\+?[0-9\- ]{7,20}$/.test(form.phone)) e.phone = "Enter a valid phone number.";
    if (form.password.length < 8) e.password = "Use at least 8 characters.";
    if (form.password !== form.confirm) e.confirm = "Passwords do not match.";
    if (isSeller && !form.business_name.trim()) e.business_name = "Business name is required.";
    return e;
  }

  async function onSubmit(ev) {
    ev.preventDefault();
    setError(null);
    const v = validate();
    setErrors(v);
    if (Object.keys(v).length) return;
    setBusy(true);
    try {
      const payload = {
        full_name: form.full_name.trim(), email: form.email, phone: form.phone, password: form.password, role,
        ...(isSeller ? { business_name: form.business_name.trim() } : {}),
      };
      const user = await register(payload);
      navigate(HOME_PATH[user.role], { replace: true });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <Card className="auth-card">
        <p><Link to="/roles">← Back to role selection</Link></p>
        <h2>{isSeller ? "Create Seller Account" : "Create Account"}</h2>
        <p className="muted">{isSeller ? "Your seller account will need admin approval before you can publish listings." : "Join FairShare as a shopper"}</p>
        <ErrorBox error={error} />
        <form onSubmit={onSubmit} noValidate>
          <FormField id="full_name" label="Full name" value={form.full_name} onChange={set("full_name")} error={errors.full_name} />
          {isSeller && <FormField id="business_name" label="Business name" value={form.business_name} onChange={set("business_name")} error={errors.business_name} />}
          <FormField id="email" label="Email address" type="email" value={form.email} onChange={set("email")} />
          <FormField id="phone" label="Phone number" type="tel" placeholder="+8801XXXXXXXXX" value={form.phone} onChange={set("phone")} error={errors.phone} />
          <FormField id="password" label="Password" type="password" autoComplete="new-password" value={form.password} onChange={set("password")} error={errors.password} />
          <FormField id="confirm" label="Confirm password" type="password" autoComplete="new-password" value={form.confirm} onChange={set("confirm")} error={errors.confirm} />
          <Button variant="primary" block type="submit" disabled={busy}>{busy ? "Creating…" : isSeller ? "Create Seller Account" : "Create User Account"}</Button>
        </form>
        <p className="muted">Already registered? <Link to={`/login/${role}`}>Sign in</Link></p>
      </Card>
    </div>
  );
}