import { BrowserRouter, Routes, Route } from "react-router-dom";
import SellerRegister from "./pages/SellerRegister";
import BusinessProfile from "./pages/BusinessProfile";
import "./App.css";

function Home() {
  return (
    <div style={{ padding: "40px", textAlign: "center" }}>
      <h1>FairShare</h1>
      <p>Welcome to FairShare</p>

      <a href="/seller/profile">
        Go to Business Profile
      </a>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />

        <Route
          path="/seller/profile"
          element={<BusinessProfile />}
        />
        <Route path="/seller/register" element={<SellerRegister />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;