import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../../context/CartContext.jsx";
import { checkout } from "../../api/cart.js";
import { formatPrice } from "../../utils/format.js";
import Button from "../../components/Button.jsx";

export default function Checkout() {
  const { cart, refresh } = useCart();
  const navigate = useNavigate();
  const [form, setForm] = useState({ shipping_address: "", phone: "", notes: "" });
  const [error, setError] = useState(null);

  if (!cart?.items?.length) return <h2>Your cart is empty.</h2>;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await checkout(form);
      await refresh(); // Clear cart context
      navigate("/app/orders");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="checkout-page" style={{ maxWidth: "600px" }}>
      <h2>Checkout</h2>
      <div style={{ marginBottom: "2rem", padding: "1rem", background: "#f1f1f1" }}>
        <h3>Order Summary</h3>
        <p>Total Items: {cart.total_items}</p>
        <p><strong>Total Amount: {formatPrice(cart.total_paisa, cart.currency)}</strong></p>
      </div>
          <div className="info-box" role="note" style={{ marginBottom: "1rem" }}>
        <strong>Simulated payment.</strong> No real money is charged and no card or mobile-banking details are collected. This only places a demo order.
      </div>
      {error && <div style={{ color: "red", marginBottom: "1rem" }}>{error}</div>}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div>
          <label style={{ display: "block", marginBottom: "5px" }}>Shipping Address *</label>
          <textarea
            required
            rows="3"
            value={form.shipping_address}
            onChange={(e) => setForm({ ...form, shipping_address: e.target.value })}
            style={{ width: "100%", padding: "8px" }}
          />
        </div>
        <div>
          <label style={{ display: "block", marginBottom: "5px" }}>Phone Number</label>
          <input
            type="text"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            style={{ width: "100%", padding: "8px" }}
          />
        </div>
        <div>
          <label style={{ display: "block", marginBottom: "5px" }}>Delivery Notes (Optional)</label>
          <input
            type="text"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            style={{ width: "100%", padding: "8px" }}
          />
        </div>
        <Button type="submit" style={{ padding: "10px" }}>Place Order (Simulated Payment)</Button>
      </form>
    </div>
  );
}