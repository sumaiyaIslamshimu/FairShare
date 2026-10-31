import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../../context/CartContext.jsx";
import { formatPrice } from "../../utils/format.js";
import { request } from "../../api/client.js"; // <-- Correctly importing 'request'
import Button from "../../components/Button.jsx";

export default function Cart() {
  const { cart, loading, update, remove } = useCart();
  const navigate = useNavigate();

  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [checkoutError, setCheckoutError] = useState(null);

  if (loading) return <div>Loading cart...</div>;
  if (!cart?.items?.length) return <h2>Your cart is empty.</h2>;

  const handleCheckout = async (e) => {
    e.preventDefault();
    setCheckoutError(null);

    if (address.trim().length < 5) {
      setCheckoutError(new Error("Shipping address must be at least 5 characters."));
      return;
    }

    setIsCheckingOut(true);
    try {
      // Using 'body' for the checkout payload
      await request('/checkout', {
        method: "POST",
        body: {
          shipping_address: address.trim(),
          phone: phone.trim() || undefined
        }
      });

      // Clear the local cart state instantly (if your useCart context supports a clear function, call it here)
      navigate('/app/orders');
    } catch (err) {
      setCheckoutError(err);
    } finally {
      setIsCheckingOut(false);
    }
  };

  return (
    <div className="cart-page" style={{ display: "flex", gap: "2rem", flexWrap: "wrap", alignItems: "flex-start" }}>

      <div className="cart-items" style={{ flex: "2 1 400px" }}>
        <h2>Shopping Cart</h2>
        {cart.items.map((item) => (
          <div key={item.seller_product_id} style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem", display: "flex", justifyContent: "space-between", borderRadius: "8px", background: "#fff" }}>
            <div>
              <h3 style={{ margin: "0 0 0.5rem 0" }}>{item.title}</h3>
              <p style={{ margin: "0 0 0.25rem 0", color: "#555" }}>Seller: {item.seller_name || item.seller_id}</p>
              <p style={{ margin: "0 0 0.5rem 0" }}>
                Price: {formatPrice(item.effective_price_paisa, item.currency)}
                {item.discount_percent > 0 && (
                  <span style={{ color: "green", marginLeft: "10px" }}>
                    ({item.discount_percent}% OFF!)
                  </span>
                )}
              </p>
              <div style={{ marginTop: "10px", display: "flex", alignItems: "center", gap: "10px" }}>
                <label>Qty: </label>
                <input
                  type="number"
                  min="1"
                  max={item.stock_qty}
                  value={item.quantity}
                  onChange={(e) => update(item.seller_product_id, parseInt(e.target.value, 10))}
                  style={{ width: "60px", padding: "0.25rem" }}
                />
                <Button onClick={() => remove(item.seller_product_id)} style={{ background: "#ef4444", color: "white", padding: "0.25rem 0.5rem", border: "none" }}>Remove</Button>
              </div>
            </div>
            <div style={{ textAlign: "right", fontWeight: "bold" }}>
              Total: {formatPrice(item.line_total_paisa, item.currency)}
            </div>
          </div>
        ))}
      </div>

      <div style={{ flex: "1 1 300px", background: "#f9f9f9", padding: "1.5rem", borderRadius: "8px", border: "1px solid #ddd" }}>
        <h2 style={{ margin: "0 0 1rem 0" }}>Order Summary</h2>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem", fontSize: "1.2rem", fontWeight: "bold" }}>
          <span>Subtotal:</span>
          <span>{formatPrice(cart.subtotal_paisa, cart.currency)}</span>
        </div>

        <form onSubmit={handleCheckout} style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1.5rem" }}>
          <div>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "500" }}>Shipping Address *</label>
            <textarea
              className="input"
              required
              rows="3"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Full delivery address (min 5 characters)"
              style={{ width: "100%", padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", resize: "vertical" }}
            />
          </div>

          <div>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "500" }}>Phone Number</label>
            <input
              className="input"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="e.g. 01700000000"
              style={{ width: "100%", padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          {checkoutError && (
            <div style={{ color: "red", background: "#fee2e2", padding: "0.75rem", borderRadius: "4px", fontSize: "0.9rem" }}>
              {checkoutError.message || checkoutError.toString()}
            </div>
          )}

          <Button type="submit" disabled={isCheckingOut} style={{ width: "100%", padding: "1rem", fontSize: "1.1rem", background: "var(--primary, #007bff)", color: "white", border: "none" }}>
            {isCheckingOut ? "Processing..." : "Place Order Now"}
          </Button>
        </form>
      </div>

    </div>
  );
}