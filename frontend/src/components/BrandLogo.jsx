
import { Link } from "react-router-dom";

export default function BrandLogo({ to = "/", showPortal = false, portalLabel = "" }) {
  return (
    <Link to={to} className="logo brand">
      <span className="logo-mark" aria-hidden="true">
        🛍️
      </span>

      <span>
        FairShare
        {showPortal && <small>{portalLabel}</small>}
      </span>
    </Link>
  );
}
