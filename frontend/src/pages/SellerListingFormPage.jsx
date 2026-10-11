import { BrowserRouter, Routes, Route } from "react-router-dom";

import ExperienceSelection from "./pages/ExperienceSelection";
import Register from "./pages/Register";
import Login from "./pages/Login";
import SellerRegister from "./pages/SellerRegister";
import BusinessProfile from "./pages/BusinessProfile";
import ProductSearchPage from "./pages/ProductSearchPage";
import ProductDetailsPage from "./pages/ProductDetailsPage";
import SellerRoute from "./components/SellerRoute";
import SellerDashboard from "./pages/SellerDashboard";
import SellerListingFormPage from "./pages/SellerListingFormPage";

import "./App.css";
import "./index.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProductSearchPage />} />

        <Route path="/experience" element={<ExperienceSelection />} />

        <Route path="/register" element={<Register />} />

        <Route path="/login" element={<Login />} />

        <Route
          path="/seller/profile"
          element={<BusinessProfile />}
        />

        <Route
          path="/seller/register"
          element={<SellerRegister />}
        />

        <Route
          path="/product/:productId"
          element={<ProductDetailsPage />}
        />

        <Route
          path="/seller/dashboard"
          element={
            <SellerRoute>
              <SellerDashboard />
            </SellerRoute>
          }
        />

        <Route
          path="/seller/listings/new"
          element={
            <SellerRoute>
              <SellerListingFormPage />
            </SellerRoute>
          }
        />

        <Route
          path="/seller/listings/:id/edit"
          element={
            <SellerRoute>
              <SellerListingFormPage />
            </SellerRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;