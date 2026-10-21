// Route table. Each member appends ONLY inside their own marked block (final edit: Member 4).
import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import PublicLayout from "./layouts/PublicLayout.jsx";
import ShopperLayout from "./layouts/ShopperLayout.jsx";
import SellerLayout from "./layouts/SellerLayout.jsx";
import AdminLayout from "./layouts/AdminLayout.jsx";
import Landing from "./pages/public/Landing.jsx";
import RoleSelect from "./pages/public/RoleSelect.jsx";
import Login from "./pages/public/Login.jsx";
import Register from "./pages/public/Register.jsx";
import AccountHome from "./pages/shared/AccountHome.jsx";
import Search from "./pages/shopper/Search.jsx";
import Compare from "./pages/shopper/Compare.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/roles" element={<RoleSelect />} />
        <Route path="/login/:role" element={<Login />} />
        <Route path="/register/:role" element={<Register />} />
      </Route>

      <Route
        path="/app"
        element={
          <ProtectedRoute roles={["user"]}>
            <ShopperLayout />
          </ProtectedRoute>
        }
      >
        {/* --- Member 1 --- */}
        <Route index element={<AccountHome />} />
        {/* --- Member 2 --- */}
        <Route path="search" element={<Search />} />
        <Route path="compare/:groupKey" element={<Compare />} />
        {/* --- Member 3 --- */}
        {/* --- Member 4 --- */}
      </Route>

      <Route
        path="/seller"
        element={
          <ProtectedRoute roles={["seller"]}>
            <SellerLayout />
          </ProtectedRoute>
        }
      >
        {/* --- Member 1 --- */}
        <Route index element={<AccountHome />} />
        {/* --- Member 2 --- */}
        {/* --- Member 3 --- */}
        {/* --- Member 4 --- */}
      </Route>

      <Route
        path="/admin"
        element={
          <ProtectedRoute roles={["admin"]}>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        {/* --- Member 1 --- */}
        <Route index element={<AccountHome />} />
        {/* --- Member 4 --- */}
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}