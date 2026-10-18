import { Link, Outlet } from "react-router-dom";
import Button from "../components/Button.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { HOME_PATH } from "../navConfig.js";

export default function PublicLayout() {
  const { user } = useAuth();
  return (
    <>
      <header className="public-nav">
        <Link to="/" className="logo">
          <span className="logo-mark">F</span>
          FairShare
        </Link>
        <div className="actions">
          {user ? (
            <Button variant="primary" to={HOME_PATH[user.role]}>Go to my account</Button>
          ) : (
            <>
              <Button to="/roles">Sign In</Button>
              <Button variant="primary" to="/roles">Get Started</Button>
            </>
          )}
        </div>
      </header>
      <Outlet />
    </>
  );
}