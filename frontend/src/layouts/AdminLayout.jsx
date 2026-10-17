import { Outlet, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import Topbar from "../components/Topbar.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { NAV } from "../navConfig.js";

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const signOut = () => {
    logout();
    navigate("/");
  };
  return (
    <div className="shell">
      <Sidebar portalLabel="Admin Panel" items={NAV.admin} onSignOut={signOut} />
      <div className="main">
        <Topbar title="Restricted Admin Panel" user={user} />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}