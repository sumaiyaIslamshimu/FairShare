
import { BrowserRouter, Routes, Route } from "react-router-dom";

import ExperienceSelection from "./pages/ExperienceSelection";
import Register from "./pages/Register";
import Login from "./pages/Login";

import SellerRegister from "./pages/SellerRegister";
import BusinessProfile from "./pages/BusinessProfile";
import ProductSearchPage from "./pages/ProductSearchPage";
import RentalDetails from "./pages/RentalDetails";
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

        {/* Seller */}
        <Route
          path="/seller/profile"
          element={<BusinessProfile />}
        />

        <Route
          path="/seller/register"
          element={<SellerRegister />}
        />

        <Route
          path="/rentals/:productId"
          element={<RentalDetails />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```
