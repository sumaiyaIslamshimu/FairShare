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

// --- Member 3 Imports ---
import Cart from "./pages/shopper/Cart.jsx";
import Checkout from "./pages/shopper/Checkout.jsx";
import Orders from "./pages/shopper/Orders.jsx";
import Insights from "./pages/seller/Insights.jsx";
import Promotions from "./pages/seller/Promotions.jsx";
import SellerOrders from "./pages/seller/SellerOrders.jsx";
import Messages from "./pages/shared/Messages.jsx";
import ShopperRentals from "./pages/shopper/Rentals.jsx";
import SellerRentals from "./pages/seller/MyRentals.jsx";

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
        <Route path="cart" element={<Cart />} />
        <Route path="checkout" element={<Checkout />} />
        <Route path="orders" element={<Orders />} />
        <Route path="messages" element={<Messages />} />
        <Route path="rentals" element={<ShopperRentals />} />
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
        <Route path="insights" element={<Insights />} />
        <Route path="promotions" element={<Promotions />} />
        <Route path="orders" element={<SellerOrders />} />
        <Route path="messages" element={<Messages />} />
        <Route path="rentals" element={<SellerRentals />} />
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