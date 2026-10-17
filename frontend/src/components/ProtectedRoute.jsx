import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { HOME_PATH } from "../navConfig.js";
import Loading from "./Loading.jsx";

// UX guard only. The backend enforces the real permissions.
export default function ProtectedRoute({ roles, children }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/roles" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={HOME_PATH[user.role] || "/"} replace />;
  return children;
}