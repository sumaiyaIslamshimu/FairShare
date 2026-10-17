import { Outlet, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import Topbar from "../components/Topbar.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { NAV } from "../navConfig.js";

export default function SellerLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const signOut = () => {
    logout();
    navigate("/");
  };
  return (
    <div className="shell">
      <Sidebar portalLabel="Seller Portal" items={NAV.seller} onSignOut={signOut} />
      <div className="main">
        <Topbar title="Seller Portal" user={user} />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}