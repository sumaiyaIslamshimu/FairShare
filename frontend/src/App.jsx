import { BrowserRouter, Routes, Route } from "react-router-dom";

// Existing Pages
import ExperienceSelection from "./pages/ExperienceSelection";
import Register from "./pages/Register";
import Login from "./pages/Login";
import SellerRegister from "./pages/SellerRegister";
import BusinessProfile from "./pages/BusinessProfile";
import ProductSearchPage from "./pages/ProductSearchPage";
import RentalDetails from "./pages/RentalDetails";

// New Pages from our current Epic
import RentalRequestsScreen from "./pages/RentalRequestsScreen";
import ListingForm from "./components/ListingForm";

import "./App.css";
import "./index.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Shopper Authentication */}
        <Route path="/" element={<ExperienceSelection />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />

        {/* Product Search */}
        <Route path="/products" element={<ProductSearchPage />} />

        {/* Seller Existing Routes */}
        <Route path="/seller/profile" element={<BusinessProfile />} />
        <Route path="/seller/register" element={<SellerRegister />} />

        {/* NEW: Seller Dashboard Routes (SCRUM-188 & 190) */}
        <Route path="/seller/requests" element={<RentalRequestsScreen />} />
        <Route path="/seller/listing/new" element={<ListingForm />} />

        {/* Rentals */}
        <Route path="/rentals/:productId" element={<RentalDetails />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;