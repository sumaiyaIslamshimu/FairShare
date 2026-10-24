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

// --- Member 4 Imports ---
import Verification from "./pages/shared/Verification.jsx";
import MyComplaints from "./pages/shared/MyComplaints.jsx";
import AdminDashboard from "./pages/admin/Dashboard.jsx";
import AdminUsers from "./pages/admin/Users.jsx";
import AdminSellerVerification from "./pages/admin/SellerVerification.jsx";
import AdminListings from "./pages/admin/Listings.jsx";
import AdminCategories from "./pages/admin/Categories.jsx";
import AdminComplaints from "./pages/admin/Complaints.jsx";
import AdminScraping from "./pages/admin/ScrapingStatus.jsx";
import AdminAudit from "./pages/admin/AuditLog.jsx";

// --- Reviews (extra scope) ---
import MyReviews from "./pages/shopper/MyReviews.jsx";
import SellerReviews from "./pages/seller/Reviews.jsx";
import AdminReviews from "./pages/admin/Reviews.jsx";
import SellerProducts from "./pages/seller/Products.jsx";
import BusinessProfile from "./pages/seller/BusinessProfile.jsx";

// --- Returns (extra scope) ---
import MyReturns from "./pages/shopper/MyReturns.jsx";
import SellerReturns from "./pages/seller/Returns.jsx";
import AdminReturns from "./pages/admin/Returns.jsx";

// --- Notifications (extra scope) ---
import Notifications from "./pages/shared/Notifications.jsx";

// --- Price tracking (extra scope) ---
import PriceWatch from "./pages/shopper/PriceWatch.jsx";

// --- Product detail (extra scope) ---
import ProductDetail from "./pages/shopper/ProductDetail.jsx";

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
        <Route path="products" element={<SellerProducts />} />
        <Route path="profile" element={<BusinessProfile />} />
        <Route path="search" element={<Search />} />
        <Route path="compare/:groupKey" element={<Compare />} />
        {/* --- Member 3 --- */}
        <Route path="cart" element={<Cart />} />
        <Route path="checkout" element={<Checkout />} />
        <Route path="orders" element={<Orders />} />
        <Route path="messages" element={<Messages />} />
        <Route path="rentals" element={<ShopperRentals />} />
        {/* --- Member 4 --- */}
        <Route path="verification" element={<Verification />} />
        <Route path="complaints" element={<MyComplaints />} />
        <Route path="reviews" element={<MyReviews />} />
        <Route path="returns" element={<MyReturns />} />
        <Route path="pricewatch" element={<PriceWatch />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="product/:id" element={<ProductDetail />} />
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
        <Route path="products" element={<SellerProducts />} />
        <Route path="profile" element={<BusinessProfile />} />
        {/* --- Member 3 --- */}
        <Route path="insights" element={<Insights />} />
        <Route path="promotions" element={<Promotions />} />
        <Route path="orders" element={<SellerOrders />} />
        <Route path="messages" element={<Messages />} />
        <Route path="rentals" element={<SellerRentals />} />
        {/* --- Member 4 --- */}
        <Route path="verification" element={<Verification />} />
        <Route path="complaints" element={<MyComplaints />} />
        <Route path="reviews" element={<SellerReviews />} />
        <Route path="returns" element={<SellerReturns />} />
        <Route path="notifications" element={<Notifications />} />
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
        <Route index element={<AdminDashboard />} />
        {/* --- Member 4 --- */}
        <Route path="users" element={<AdminUsers />} />
        <Route path="verification" element={<AdminSellerVerification />} />
        <Route path="listings" element={<AdminListings />} />
        <Route path="categories" element={<AdminCategories />} />
        <Route path="complaints" element={<AdminComplaints />} />
        <Route path="reviews" element={<AdminReviews />} />
        <Route path="scraping" element={<AdminScraping />} />
        <Route path="audit" element={<AdminAudit />} />
        <Route path="returns" element={<AdminReturns />} />
        <Route path="notifications" element={<Notifications />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}