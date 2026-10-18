import { useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { HOME_PATH } from "../../navConfig.js";

const TITLES = { user: "shopper", seller: "seller", admin: "admin" };

export default function Login() {
  const { role } = useParams();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  if (!TITLES[role]) return <Navigate to="/roles" replace />;

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const user = await login(email, password, role);
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
        <h2>{role === "admin" ? "Admin Sign In" : "Welcome back"}</h2>
        <p className="muted">Sign in to your {TITLES[role]} account</p>
        <ErrorBox error={error} />
        <form onSubmit={onSubmit}>
          <FormField id="email" label="Email address" type="email" required autoComplete="email"
            value={email} onChange={(e) => setEmail(e.target.value)} />
          <FormField id="password" label="Password">
            <div className="pw-row">
              <input id="password" className="input" type={show ? "text" : "password"} required
                autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button type="button" onClick={() => setShow(!show)}>{show ? "Hide" : "Show"}</button>
            </div>
          </FormField>
          <Button variant="primary" block type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign In"}</Button>
        </form>
        {role !== "admin" && (
          <p className="muted">Don't have an account? <Link to={`/register/${role}`}>Create one</Link></p>
        )}
      </Card>
    </div>
  );
}